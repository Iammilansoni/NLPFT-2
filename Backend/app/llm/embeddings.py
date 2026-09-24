"""
Embedding clients
=================

Turns text into vectors with any provider in the registry that offers
embeddings, over its own protocol:

    ollama       POST {host}/api/embed
    builtin      fastembed ONNX, in-process (no server, no key)
    gemini       POST models/{id}:batchEmbedContents
    openai       POST {base}/embeddings   (OpenAI, OpenRouter, Mistral, Together,
                                            Fireworks, DeepInfra, NVIDIA, Cohere,
                                            Jina, Nebius, Novita, custom servers)
    huggingface  POST router.huggingface.co/hf-inference/models/{id}/pipeline/feature-extraction

Free tiers rate-limit bulk embedding, so every remote call goes through
`_post_json`, which honours Retry-After and backs off exponentially before
giving up with a message a user can act on.
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import Any, Dict, List, Optional, Sequence

import httpx

from app.core.logger import logger
from app.llm import provider_registry as registry
from app.llm.model_discovery import (
    DiscoveryError,
    check_base_url,
    error_detail,
    ollama_base_url,
    resolved_base_url,
)
from app.llm.provider_registry import ProviderSpec

EMBED_TIMEOUT = float(os.getenv("EMBED_TIMEOUT", "120"))
MAX_RETRIES = int(os.getenv("EMBED_MAX_RETRIES", "6"))
BATCH_SIZE_OVERRIDE = int(os.getenv("EMBED_BATCH_SIZE", "0"))
BUILTIN_CACHE_DIR = os.getenv("ONNX_CACHE_DIR", "/opt/models/fastembed")


class EmbeddingError(Exception):
    """Embedding failed. `message` is written for the end user."""

    def __init__(self, message: str, code: str = "EMBEDDING_FAILED") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def batch_size_for(provider: str) -> int:
    if BATCH_SIZE_OVERRIDE > 0:
        return BATCH_SIZE_OVERRIDE
    spec = registry.get_provider(provider)
    return spec.embed_batch if spec else 64


async def _post_json(
    client: httpx.AsyncClient,
    spec: ProviderSpec,
    url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    """POST with retries on rate limits and transient server errors."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            if attempt == MAX_RETRIES:
                raise EmbeddingError(f"{spec.label} did not answer within {EMBED_TIMEOUT:.0f}s.", "UNREACHABLE") from exc
            response = None
        except httpx.HTTPError as exc:
            raise EmbeddingError(f"Couldn't reach {spec.label}. Check the address and your network.", "UNREACHABLE") from exc

        retryable = response is None or response.status_code == 429 or response.status_code >= 500
        if response is not None and not retryable:
            if response.status_code >= 400:
                _raise_for_status(spec, response)
            try:
                return response.json()
            except ValueError as exc:
                raise EmbeddingError(f"{spec.label} returned something that isn't JSON.", "BAD_RESPONSE") from exc
        if attempt == MAX_RETRIES:
            if response is not None and response.status_code == 429:
                raise EmbeddingError(
                    f"{spec.label} kept rate-limiting after {MAX_RETRIES} retries. Free tiers allow a limited "
                    "number of requests per minute: try again later, or use a paid key or a local model.",
                    "RATE_LIMITED",
                )
            if response is not None:
                _raise_for_status(spec, response)
        delay = _retry_delay(response, attempt)
        logger.warning(
            f"{spec.label} embedding call {'rate-limited' if response is not None and response.status_code == 429 else 'failed'}"
            f" (attempt {attempt + 1}/{MAX_RETRIES + 1}); retrying in {delay:.1f}s"
        )
        await asyncio.sleep(delay)
    raise EmbeddingError(f"{spec.label} embedding failed.")  # unreachable


def _retry_delay(response: Optional[httpx.Response], attempt: int) -> float:
    if response is not None:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return min(float(retry_after), 120.0)
            except ValueError:
                pass
    return min(2 ** attempt + random.uniform(0, 1), 60.0)


def _raise_for_status(spec: ProviderSpec, response: httpx.Response) -> None:
    detail = error_detail(response)
    if response.status_code in (401, 403) or "api key" in detail.lower():
        raise EmbeddingError(f"{spec.label} rejected the API key. Check it in Settings → AI Providers.", "AUTH")
    if response.status_code == 404 or "not found" in detail.lower():
        raise EmbeddingError(f"{spec.label} does not serve this model{': ' + detail if detail else ''}.", "MODEL_NOT_FOUND")
    suffix = f": {detail}" if detail else ""
    raise EmbeddingError(f"{spec.label} returned HTTP {response.status_code} while embedding{suffix}", "BAD_RESPONSE")


# ---------------------------------------------------------------------------
# Per-protocol calls (one batch each)
# ---------------------------------------------------------------------------

async def _embed_ollama(client, spec, model_id, texts, api_key, base_url) -> List[List[float]]:
    data = await _post_json(client, spec, f"{ollama_base_url(base_url)}/api/embed", {"model": model_id, "input": list(texts)})
    return data.get("embeddings") or []


async def _embed_openai(client, spec, model_id, texts, api_key, base_url) -> List[List[float]]:
    base = resolved_base_url(spec, base_url)
    if not base:
        raise EmbeddingError(f"{spec.label} needs a server URL.", "NO_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    payload = {"model": model_id, "input": list(texts), **spec.embed_extra}
    data = await _post_json(client, spec, f"{base}/embeddings", payload, headers)
    items = sorted(data.get("data") or [], key=lambda d: d.get("index", 0))
    return [item.get("embedding") or [] for item in items]


async def _embed_gemini(client, spec, model_id, texts, api_key, base_url) -> List[List[float]]:
    name = model_id if model_id.startswith("models/") else f"models/{model_id}"
    payload = {"requests": [{"model": name, "content": {"parts": [{"text": t}]}} for t in texts]}
    data = await _post_json(
        client, spec, f"{spec.base_url}/{name}:batchEmbedContents", payload, {"x-goog-api-key": api_key or ""}
    )
    return [e.get("values") or [] for e in data.get("embeddings") or []]


async def _embed_huggingface(client, spec, model_id, texts, api_key, base_url) -> List[List[float]]:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    url = f"{spec.base_url}/hf-inference/models/{model_id}/pipeline/feature-extraction"
    data = await _post_json(client, spec, url, {"inputs": list(texts)}, headers)
    vectors = []
    for item in data:
        # Some models return token-level vectors; mean-pool them to one per text.
        if item and isinstance(item[0], list):
            width = len(item[0])
            item = [sum(tok[i] for tok in item) / len(item) for i in range(width)]
        vectors.append(item)
    return vectors


_BUILTIN_MODELS: Dict[str, Any] = {}
_BUILTIN_LOCK = asyncio.Lock()


async def _embed_builtin(client, spec, model_id, texts, api_key, base_url) -> List[List[float]]:
    async with _BUILTIN_LOCK:
        model = _BUILTIN_MODELS.get(model_id)
        if model is None:
            def load():
                from fastembed import TextEmbedding

                os.makedirs(BUILTIN_CACHE_DIR, exist_ok=True)
                return TextEmbedding(model_name=model_id, cache_dir=BUILTIN_CACHE_DIR)

            try:
                logger.info(f"Loading built-in ONNX embedding model {model_id} (downloads on first use)")
                model = await asyncio.to_thread(load)
            except ImportError as exc:
                raise EmbeddingError("Built-in models need the fastembed package, which this image does not include.", "UNSUPPORTED") from exc
            except Exception as exc:  # noqa: BLE001 - fastembed raises plain exceptions for unknown models
                raise EmbeddingError(f"The built-in model '{model_id}' could not be loaded: {exc}", "MODEL_NOT_FOUND") from exc
            _BUILTIN_MODELS[model_id] = model
    # ONNX inference is CPU-bound: keep it off the event loop.
    return await asyncio.to_thread(lambda: [v.tolist() for v in model.embed(list(texts))])


_EMBEDDERS = {
    registry.OLLAMA: _embed_ollama,
    registry.BUILTIN: _embed_builtin,
    registry.GEMINI: _embed_gemini,
    registry.OPENAI: _embed_openai,
    registry.CUSTOM: _embed_openai,
    registry.HUGGINGFACE: _embed_huggingface,
}


async def embed_texts(
    provider: str,
    model_id: str,
    texts: Sequence[str],
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[List[float]]:
    """Embed `texts` in provider-sized batches. Raises EmbeddingError."""
    spec = registry.get_provider(provider)
    if spec is None or not spec.embeddings:
        raise EmbeddingError(f"{registry.provider_label(provider)} does not offer embedding models.", "UNSUPPORTED")
    if spec.requires_key and not api_key:
        raise EmbeddingError(
            f"Using {spec.label} needs an API key. Add yours in Settings → AI Providers.", "NO_KEY"
        )
    try:
        base_url = await asyncio.to_thread(check_base_url, provider, base_url)
    except DiscoveryError as exc:
        raise EmbeddingError(exc.message, exc.code) from exc
    call = _EMBEDDERS[spec.api]
    size = batch_size_for(provider)
    vectors: List[List[float]] = []
    async with httpx.AsyncClient(timeout=EMBED_TIMEOUT) as client:
        for start in range(0, len(texts), size):
            batch = list(texts[start : start + size])
            out = await call(client, spec, model_id, batch, api_key, base_url)
            if len(out) != len(batch) or any(not v for v in out):
                raise EmbeddingError(
                    f"{spec.label} returned {len(out)} vectors for {len(batch)} texts with '{model_id}'.",
                    "BAD_RESPONSE",
                )
            vectors.extend(out)
    return vectors
