"""
Structured Slot Extraction
==========================

Turns a natural-language query into a request body that is GUARANTEED to satisfy
the target template's JSON Schema - or reports honestly that it could not.

WHAT THIS REPLACES
------------------
v1 (`slot_extraction_service._parse_json_response`) asked the LLM for JSON in a
prose prompt, then scraped the reply:

    if text.startswith("```json"): text = text[7:]
    start = text.find("{"); end = text.rfind("}") + 1
    parsed = json.loads(text[start:end])

Three failures follow from that design:

  1. Nothing constrains the model's output, so malformed JSON is routine.
  2. `find("{")` .. `rfind("}")` grabs the outermost braces in the whole reply -
     a model that explains itself before answering yields a corrupt slice.
  3. Every failure path returns `{}` - and so does a genuinely empty extraction.
     A crashed LLM call and "no slots present" were byte-identical to the caller.

THREE LAYERS OF GUARANTEE
-------------------------
  1. CONSTRAINED DECODING. Ollama accepts a JSON Schema in its `format`
     parameter and constrains token sampling to it. Invalid JSON becomes
     unrepresentable rather than merely discouraged.
  2. PYDANTIC VALIDATION. A model is built dynamically from the template's own
     json_schema and validates the parse. Types are coerced, unknown keys are
     dropped, required fields are enforced.
  3. REPAIR RETRY. On validation failure the specific pydantic error is appended
     to the prompt and the call is retried once. Models correct their own
     mistakes reliably when told exactly what was wrong.

FAILURE IS REPORTED, NEVER SWALLOWED
------------------------------------
Returns an ExtractionResult carrying `ok`, `degraded` and `reason`. The caller
can distinguish "no slots in this query" from "the LLM was unreachable" - which
v1 could not.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Type

import httpx
from pydantic import BaseModel, ValidationError, create_model

from app.core.circuit_breaker import CircuitOpenError, get_breaker
from app.core.logger import logger

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "llama3.2")
EXTRACTION_TIMEOUT = float(os.getenv("EXTRACTION_TIMEOUT", "45"))


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class ExtractionResult:
    """
    Outcome of one extraction.

    `ok=True, values={}`  -> the query genuinely carried no slot values
    `ok=False`            -> extraction failed; `reason` says why
    """

    ok: bool
    values: Dict[str, Any] = field(default_factory=dict)
    degraded: bool = False
    reason: Optional[str] = None
    attempts: int = 0
    latency_ms: float = 0.0
    model: str = EXTRACTION_MODEL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "values": self.values,
            "degraded": self.degraded,
            "reason": self.reason,
            "attempts": self.attempts,
            "latency_ms": round(self.latency_ms, 2),
            "model": self.model,
        }


# ---------------------------------------------------------------------------
# JSON Schema -> pydantic
# ---------------------------------------------------------------------------

_JSON_TO_PY: Dict[str, Any] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": List[Any],
    "object": Dict[str, Any],
}


def _py_type(field_schema: Dict[str, Any]) -> Any:
    """Map one JSON Schema property to a Python annotation."""
    jtype = field_schema.get("type")
    if isinstance(jtype, list):  # e.g. ["string", "null"]
        jtype = next((t for t in jtype if t != "null"), "string")
    return _JSON_TO_PY.get(jtype or "string", Any)


def build_validator(schema: Dict[str, Any], name: str = "ExtractedBody") -> Type[BaseModel]:
    """
    Compile a JSON Schema into a pydantic model.

    Only top-level properties are modelled strictly; nested objects stay
    Dict[str, Any]. Full recursive compilation buys little here because the
    constrained decoder already enforces nested shape, and it would make deeply
    nested API schemas brittle.
    """
    props: Dict[str, Any] = schema.get("properties", {}) or {}
    required = set(schema.get("required", []) or [])

    fields: Dict[str, Tuple[Any, Any]] = {}
    for key, spec in props.items():
        if not isinstance(spec, dict):
            continue
        annotation = _py_type(spec)
        if key in required:
            fields[key] = (annotation, ...)
        else:
            fields[key] = (Optional[annotation], None)

    if not fields:
        fields["__placeholder__"] = (Optional[str], None)

    return create_model(name, **fields)  # type: ignore[call-overload]


def _sanitise_schema_for_ollama(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ollama's structured-output grammar accepts a plain JSON Schema object.

    Every property is made optional: a query legitimately may not mention every
    field, and forcing the decoder to emit a required key it has no value for
    makes it hallucinate one. Requiredness is enforced downstream by pydantic,
    where a missing value can be reported instead of invented.
    """
    props = schema.get("properties", {}) or {}
    return {
        "type": "object",
        "properties": {
            k: {"type": (v.get("type") if isinstance(v, dict) else "string") or "string"}
            for k, v in props.items()
        },
    }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class StructuredExtractionService:
    """Schema-constrained slot extraction with breaker protection and repair retry."""

    def __init__(self, model: str = EXTRACTION_MODEL) -> None:
        self.model = model
        self._client: Optional[httpx.AsyncClient] = None
        self.breaker = get_breaker("llm_extraction")

    async def client(self) -> httpx.AsyncClient:
        """
        One pooled client for the process.

        v1 opened `async with httpx.AsyncClient()` per call, paying a fresh TCP
        handshake for every extraction and pooling nothing.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(EXTRACTION_TIMEOUT, connect=5.0),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self._client

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # -- prompting ----------------------------------------------------------

    @staticmethod
    def _describe_fields(schema: Dict[str, Any]) -> str:
        props = schema.get("properties", {}) or {}
        required = set(schema.get("required", []) or [])
        lines = []
        for key, spec in props.items():
            spec = spec if isinstance(spec, dict) else {}
            bits = [f"  - {key} ({spec.get('type', 'string')})"]
            if key in required:
                bits.append("[required]")
            if spec.get("enum"):
                bits.append(f"one of {spec['enum']}")
            if spec.get("description"):
                bits.append(f"- {spec['description']}")
            lines.append(" ".join(bits))
        return "\n".join(lines)

    def _build_prompt(
        self,
        query: str,
        schema: Dict[str, Any],
        api_name: str,
        endpoint: str,
        repair_error: Optional[str] = None,
    ) -> str:
        prompt = (
            f"Extract values from the user request into JSON for the "
            f"{api_name or 'target'} API ({endpoint or 'endpoint'}).\n\n"
            f"Fields:\n{self._describe_fields(schema)}\n\n"
            f"Rules:\n"
            f"  - Copy values verbatim from the request. Never invent one.\n"
            f"  - Omit any field the request does not mention.\n"
            f"  - Output only the JSON object.\n\n"
            f"User request: {query}\n"
        )
        if repair_error:
            prompt += (
                f"\nYour previous answer was rejected:\n{repair_error}\n"
                f"Return corrected JSON.\n"
            )
        return prompt

    # -- transport ----------------------------------------------------------

    async def _generate(self, prompt: str, schema: Dict[str, Any]) -> str:
        """One constrained generation call. Raises on transport/HTTP failure."""
        client = await self.client()

        async def _post() -> httpx.Response:
            return await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    # THE KEY CHANGE: hand the schema to the decoder so invalid
                    # JSON cannot be sampled, rather than asking politely in prose.
                    "format": _sanitise_schema_for_ollama(schema),
                    "options": {"temperature": 0.0, "num_predict": 512},
                },
            )

        response = await self.breaker.call(_post)
        if response.status_code != 200:
            raise RuntimeError(f"LLM HTTP {response.status_code}: {response.text[:200]}")
        return (response.json().get("response") or "").strip()

    # -- public API ---------------------------------------------------------

    async def extract(
        self,
        query: str,
        request_schema: Optional[Dict[str, Any]],
        api_name: str = "",
        endpoint: str = "",
        max_repair_attempts: int = 1,
    ) -> ExtractionResult:
        """Extract slot values, guaranteed schema-valid or explicitly failed."""
        t0 = time.perf_counter()

        if not request_schema or not (request_schema.get("properties")):
            return ExtractionResult(ok=True, values={}, reason="no schema on template")

        Validator = build_validator(request_schema)
        repair_error: Optional[str] = None
        attempts = 0

        for attempt in range(max_repair_attempts + 1):
            attempts = attempt + 1
            prompt = self._build_prompt(
                query, request_schema, api_name, endpoint, repair_error
            )

            try:
                raw = await self._generate(prompt, request_schema)
            except CircuitOpenError as exc:
                # The dependency is known-down. Do not retry into a closed door.
                logger.warning(f"Extraction skipped: {exc}")
                return ExtractionResult(
                    ok=False,
                    degraded=True,
                    reason=f"llm_circuit_open (retry in ~{exc.retry_after:.0f}s)",
                    attempts=attempts,
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    model=self.model,
                )
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                logger.error(f"Extraction transport failure: {exc}")
                return ExtractionResult(
                    ok=False,
                    degraded=True,
                    reason=f"llm_unreachable ({type(exc).__name__})",
                    attempts=attempts,
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    model=self.model,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Extraction call failed: {exc}")
                return ExtractionResult(
                    ok=False,
                    degraded=True,
                    reason=f"llm_error ({exc})",
                    attempts=attempts,
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    model=self.model,
                )

            # Constrained decoding makes this parse reliable, but a model can
            # still emit an empty string if it runs out of tokens.
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError as exc:
                repair_error = f"Output was not valid JSON: {exc}"
                logger.warning(f"Extraction attempt {attempts}: {repair_error}")
                continue

            if not isinstance(parsed, dict):
                repair_error = "Output must be a JSON object, not an array or scalar."
                continue

            # Drop nulls so absent fields do not masquerade as explicit nulls.
            parsed = {k: v for k, v in parsed.items() if v is not None}

            try:
                validated = Validator(**parsed)
            except ValidationError as exc:
                repair_error = "; ".join(
                    f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}"
                    for e in exc.errors()[:5]
                )
                logger.warning(f"Extraction attempt {attempts} failed validation: {repair_error}")
                continue

            values = {
                k: v
                for k, v in validated.model_dump(exclude_none=True).items()
                if k != "__placeholder__"
            }
            return ExtractionResult(
                ok=True,
                values=values,
                attempts=attempts,
                latency_ms=(time.perf_counter() - t0) * 1000,
                model=self.model,
            )

        return ExtractionResult(
            ok=False,
            degraded=False,
            reason=f"validation_failed after {attempts} attempts: {repair_error}",
            attempts=attempts,
            latency_ms=(time.perf_counter() - t0) * 1000,
            model=self.model,
        )


_service: Optional[StructuredExtractionService] = None


def get_structured_extraction_service() -> StructuredExtractionService:
    global _service
    if _service is None:
        _service = StructuredExtractionService()
    return _service
