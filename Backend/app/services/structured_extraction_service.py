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

HYBRID STRATEGY (the default)
-----------------------------
Measured on evals/extraction_cases.py, the model alone invented 55 values in
100 requests (an example.com email, "some_token", the request pasted into a
password field) and took ~2 s per request. So extraction now runs in order:

  1. RULES (app.services.extraction_rules): values readable straight off the
     request from the schema's own field names, types, formats and enums.
     Exact, instant, confidence 0.99. Often nothing is left for the model.
  2. MODEL, only for fields the rules did not fill, and only when the request
     still has words the rules did not account for.
  3. GROUNDING: each model value must be supported by the request. Values that
     aren't are returned as `unverified`, never as extracted fact.

Every extracted field carries its source ("rule" | "llm") and a confidence.
The model is the user's own chat connection when they have one, else the local
Ollama model: no API key is ever required.

FAILURE IS REPORTED, NEVER SWALLOWED
------------------------------------
Returns an ExtractionResult carrying `ok`, `degraded` and `reason`. The caller
can distinguish "no slots in this query" from "the LLM was unreachable" - which
v1 could not.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple, Type

import httpx
from pydantic import BaseModel, ValidationError, create_model

from app.core.circuit_breaker import CircuitOpenError, get_breaker
from app.core.logger import logger
from app.services.extraction_rules import (
    STOPWORDS,
    FieldValue,
    command_words,
    confidence_for,
    extract_by_rules,
    grounding_problem,
    refine_llm_value,
)

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "llama3.2:3b")
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
    model: Optional[str] = EXTRACTION_MODEL
    # Required fields the request never mentioned. Reported, never invented.
    missing_required: List[str] = field(default_factory=list)
    # Per extracted field: its value, source ("rule" | "llm") and confidence.
    fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Values the model proposed that the request does not support, with why.
    unverified: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    strategy: str = "llm"

    @property
    def confidence(self) -> Optional[float]:
        """The weakest extracted field's confidence: a body is only as sure as its least sure value."""
        return min((f["confidence"] for f in self.fields.values()), default=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "values": self.values,
            "missing_required": self.missing_required,
            "fields": self.fields,
            "unverified": self.unverified,
            "confidence": self.confidence,
            "strategy": self.strategy,
            "degraded": self.degraded,
            "reason": self.reason,
            "attempts": self.attempts,
            "latency_ms": round(self.latency_ms, 2),
            "model": self.model,
        }


_PLACEHOLDERS = {"", "null", "none", "n/a", "na", "unknown", "not provided", "not specified", "<string>", "string"}


def _is_absent(value: Any) -> bool:
    """True for values that mean "the request did not say"."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in _PLACEHOLDERS
    return False


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


def _coerce(value: Any, spec: Dict[str, Any]) -> Tuple[Any, Optional[str]]:
    """Coerce one model value to its schema type; (value, problem)."""
    try:
        Single = create_model("Single", v=(_py_type(spec), ...))  # type: ignore[call-overload]
        return Single(v=value).v, None
    except ValidationError:
        return value, f"not a valid {spec.get('type', 'value')}"


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
# Models
# ---------------------------------------------------------------------------

class ExtractionLLM(Protocol):
    """A model that answers an extraction prompt with a JSON object."""

    name: str

    async def generate_json(self, prompt: str, schema: Dict[str, Any]) -> str: ...


class ProviderExtractionLLM:
    """
    Extraction through a user's own chat connection (Groq, Gemini, OpenRouter, ...).

    Hosted APIs don't share one way of constraining output to a schema, so the
    reply is parsed and validated instead; grounding then checks every value.
    """

    def __init__(self, provider: Any, label: str) -> None:
        self.provider = provider
        self.name = label

    async def generate_json(self, prompt: str, schema: Dict[str, Any]) -> str:
        from app.llm.providers.base import LLMConfig

        # Interactive path: a slow hosted call falls back to the local model
        # instead of holding the request for the provider's full timeout.
        response = await asyncio.wait_for(
            self.provider.generate(
                prompt + "\nAnswer with the JSON object only, no prose, no code fences.",
                config=LLMConfig(temperature=0.0, max_tokens=512),
            ),
            timeout=EXTRACTION_TIMEOUT,
        )
        text = (response.content or "").strip()
        fenced = re.search(r"\{.*\}", text, flags=re.S)
        return fenced.group(0) if fenced else text


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

    async def warm(self) -> bool:
        """
        Load the model into Ollama's memory ahead of the first request.

        On CPU, loading a 3B model takes tens of seconds; paying that inside a
        user's first request would exceed EXTRACTION_TIMEOUT and report a
        spurious llm_unreachable. An empty prompt loads without generating.
        """
        try:
            client = await self.client()
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": self.model, "prompt": "", "keep_alive": "24h"},
                timeout=httpx.Timeout(300.0, connect=5.0),
            )
            ok = response.status_code == 200
            logger.info(f"Extraction model {self.model} warm: {ok}")
            return ok
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Extraction model warm-up failed: {exc}")
            return False

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
        strategy: str = "hybrid",
        llm: Optional[ExtractionLLM] = None,
    ) -> ExtractionResult:
        """
        Extract slot values.

        strategy "hybrid" (default): rules, then the model for what is left,
        then grounding. "rules": no model. "llm": the model alone (the v2
        behaviour, kept so the benchmark can compare against it).
        """
        if not request_schema or not (request_schema.get("properties")):
            return ExtractionResult(ok=True, values={}, reason="no schema on template", strategy=strategy, model=None)
        if strategy in ("hybrid", "rules"):
            return await self._extract_hybrid(query, request_schema, api_name, endpoint, strategy, llm)
        return await self._extract_llm_only(query, request_schema, api_name, endpoint, max_repair_attempts)

    # -- hybrid -------------------------------------------------------------

    async def _extract_hybrid(
        self,
        query: str,
        schema: Dict[str, Any],
        api_name: str,
        endpoint: str,
        strategy: str,
        llm: Optional[ExtractionLLM],
    ) -> ExtractionResult:
        t0 = time.perf_counter()
        props: Dict[str, Dict[str, Any]] = {
            k: v for k, v in (schema.get("properties") or {}).items() if isinstance(v, dict)
        }
        required = [k for k in (schema.get("required") or []) if k in props]
        found: Dict[str, FieldValue] = extract_by_rules(query, schema)
        unverified: Dict[str, Dict[str, Any]] = {}
        remaining = [k for k in props if k not in found]
        known = {k: fv.value for k, fv in found.items()}
        command = command_words(api_name, endpoint, schema, known)

        # Words the rules didn't account for. None left means nothing else was
        # said, so asking a model could only produce invented values.
        leftover = set(re.findall(r"[a-z0-9]+", query.lower())) - command - STOPWORDS
        attempts, model_name, degraded, reason = 0, None, False, None

        if strategy == "hybrid" and remaining and leftover:
            sub_schema = {"type": "object", "properties": {k: props[k] for k in remaining}}
            prompt = self._build_prompt(query, sub_schema, api_name, endpoint)
            if known:
                prompt += "\nAlready extracted (do not repeat): " + json.dumps(known) + "\n"
            parsed, attempts, model_name, degraded, reason = await self._ask_model(prompt, sub_schema, llm)
            for key, value in parsed.items():
                if key not in remaining or _is_absent(value) or value in ([], {}):
                    continue
                coerced, problem = _coerce(value, props[key])
                coerced = refine_llm_value(key, coerced, props[key], query, command)
                problem = problem or grounding_problem(key, coerced, props[key], query, command)
                if problem:
                    unverified[key] = {"value": coerced, "reason": problem}
                else:
                    found[key] = FieldValue(coerced, "llm", confidence_for(props[key]))

        missing = [k for k in required if k not in found]
        return ExtractionResult(
            ok=not missing and not degraded,
            values={k: fv.value for k, fv in found.items()},
            fields={k: fv.to_dict() for k, fv in found.items()},
            unverified=unverified,
            missing_required=missing,
            degraded=degraded,
            reason=reason or (f"missing required: {', '.join(missing)}" if missing else None),
            attempts=attempts,
            latency_ms=(time.perf_counter() - t0) * 1000,
            model=model_name,
            strategy=strategy,
        )

    async def _ask_model(
        self, prompt: str, schema: Dict[str, Any], llm: Optional[ExtractionLLM]
    ) -> Tuple[Dict[str, Any], int, Optional[str], bool, Optional[str]]:
        """
        One JSON answer from the user's model, else the local one. Returns
        (parsed, attempts, model, degraded, reason). Retries once on bad JSON.
        """
        candidates: List[Tuple[str, Any]] = []
        if llm is not None:
            candidates.append((llm.name, llm.generate_json))
        candidates.append((f"ollama/{self.model}", self._generate))
        attempts = 0
        last_problem = None
        for name, generate in candidates:
            repair = None
            for _ in range(2):
                attempts += 1
                try:
                    raw = await generate(prompt + (f"\nYour previous answer was not valid JSON ({repair}). Return only the JSON object.\n" if repair else ""), schema)
                except CircuitOpenError as exc:
                    last_problem = f"llm_circuit_open (retry in ~{exc.retry_after:.0f}s)"
                    break
                except Exception as exc:  # noqa: BLE001 - try the next model
                    last_problem = f"llm_unreachable ({name}: {type(exc).__name__})"
                    logger.warning(f"Extraction with {name} failed: {exc}")
                    break
                try:
                    parsed = json.loads(raw) if raw else {}
                except json.JSONDecodeError as exc:
                    repair = str(exc)
                    continue
                if isinstance(parsed, dict):
                    return parsed, attempts, name, False, None
                repair = "the answer must be a JSON object"
            if repair and last_problem is None:
                last_problem = f"invalid_json from {name}"
        return {}, attempts, None, True, last_problem

    # -- model only (v2 behaviour) -----------------------------------------

    async def _extract_llm_only(
        self,
        query: str,
        request_schema: Dict[str, Any],
        api_name: str,
        endpoint: str,
        max_repair_attempts: int,
    ) -> ExtractionResult:
        """The model alone, schema-constrained and validated, without rules or grounding."""
        t0 = time.perf_counter()

        Validator = build_validator(request_schema)
        known_keys = set((request_schema.get("properties") or {}).keys())
        required = list(request_schema.get("required") or [])
        repair_error: Optional[str] = None
        last_parsed: Dict[str, Any] = {}
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

            # Drop nulls AND blank / placeholder strings so an absent field is
            # reported as missing instead of passing validation with an invented
            # value. Small models under a schema constraint tend to fill a
            # required string they have no value for with " " or "N/A".
            parsed = {k: v for k, v in parsed.items() if not _is_absent(v)}
            last_parsed = {k: v for k, v in parsed.items() if k in known_keys}

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

        # Validation never passed. Most often the request simply did not mention a
        # required field ("log me in as dana@shop.io" has no password). Return what
        # WAS extracted plus exactly which required fields are absent, rather than
        # discarding correct values or inventing the missing ones.
        return ExtractionResult(
            ok=False,
            degraded=False,
            values=last_parsed,
            missing_required=[k for k in required if k not in last_parsed],
            reason=f"validation_failed after {attempts} attempts: {repair_error}",
            attempts=attempts,
            latency_ms=(time.perf_counter() - t0) * 1000,
            model=self.model,
        )


async def user_extraction_llm(db: Any, user_id: Any) -> Optional[ProviderExtractionLLM]:
    """
    The user's default chat connection, used for extraction when they have one.

    Optional by design: with no connection (or EXTRACTION_USE_USER_LLM=false)
    extraction runs on the local model and needs no API key at all.
    """
    if os.getenv("EXTRACTION_USE_USER_LLM", "true").lower() not in ("1", "true", "yes"):
        return None
    from app.llm.provider_registry import get_provider
    from app.services.llm_config_service import LLMConfigService

    service = LLMConfigService(db)
    config = await service.get_default_config(user_id)
    spec = get_provider(config.provider) if config else None
    if not config or not spec or not spec.chat:
        return None
    if config.provider == "ollama" and config.model_name == EXTRACTION_MODEL and not config.base_url:
        return None  # identical to the local default, which also gets schema-constrained decoding
    try:
        provider = await service.get_provider_for_config(config.config_id)
    except Exception as exc:  # noqa: BLE001 -- fall back to the local model
        logger.warning(f"Extraction: user connection {config.config_id} unusable ({exc}); using the local model")
        return None
    return ProviderExtractionLLM(provider, f"{config.provider}/{config.model_name}")


_service: Optional[StructuredExtractionService] = None


def get_structured_extraction_service() -> StructuredExtractionService:
    global _service
    if _service is None:
        _service = StructuredExtractionService()
    return _service
