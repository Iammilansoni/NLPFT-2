"""
Live model discovery
====================

Asks each provider which models it serves *right now*, instead of shipping a
hand-maintained list that is stale the week after it is written. The model
catalogue (`app.services.model_catalog_service`) calls this on a schedule and
when a user saves a connection; the settings UI reads the catalogue.

Providers are described in `provider_registry`; listing is done per wire
protocol, so every OpenAI-compatible provider shares one lister.

Every lister returns `DiscoveredModel`s with the same shape:

    kind        "llm" or "embedding" -- decided from what the provider reports
                (Ollama capabilities, Gemini supportedGenerationMethods, a
                model `type`, output modalities), with a name heuristic only
                for listings that carry no capability data.
    dimension   embedding width. Taken from provider metadata when it exists
                (Ollama, the built-in ONNX models); otherwise measured by
                `probe_dimension`, never guessed from the model name.

A failed listing raises `DiscoveryError` with a sentence a user can act on.
Callers must treat a failure as "we don't know", never as "the provider has no
models" -- the catalogue relies on that to avoid retiring everything during an
outage.
"""

from __future__ import annotations

import asyncio
import ipaddress
import os
import socket
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Awaitable, Callable, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from app.core.logger import logger
from app.llm import provider_registry as registry
from app.llm.provider_registry import ProviderSpec, provider_label

REQUEST_TIMEOUT = float(os.getenv("MODEL_DISCOVERY_TIMEOUT", "20"))
HUGGINGFACE_HUB_URL = "https://huggingface.co/api"

# Model families that cannot answer a text prompt or embed text. Only consulted
# when the provider gives no capability metadata.
_NON_TEXT_MARKERS = (
    "whisper", "tts", "transcribe", "audio", "realtime", "dall-e", "image",
    "moderation", "guard", "orpheus", "sora", "playai", "computer-use",
    "search-preview", "veo", "imagen", "lyria", "native-audio", "rerank",
    "ocr", "flux", "stable-diffusion", "sdxl", "vision-only",
)
# Values of a listing's `type` field (Together, Jina, ...).
_EMBEDDING_TYPES = {"embedding", "embeddings", "text-embedding"}
_CHAT_TYPES = {"chat", "language", "llm", "text", "code", "completion"}


@dataclass
class DiscoveredModel:
    model_id: str
    kind: str  # "llm" | "embedding"
    display_name: str
    description: str = ""
    context_tokens: Optional[int] = None
    dimension: Optional[int] = None
    is_local: bool = False
    is_free: Optional[bool] = None
    shutdown_date: Optional[date] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DiscoveryError(Exception):
    """A provider listing failed. `message` is written for the end user."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code  # AUTH | UNREACHABLE | RATE_LIMITED | BAD_RESPONSE | NO_KEY | UNSUPPORTED


def _classify_by_name(model_id: str) -> Optional[str]:
    lowered = model_id.lower()
    if "embed" in lowered:
        return "embedding"
    if any(marker in lowered for marker in _NON_TEXT_MARKERS):
        return None
    return "llm"


def _is_text_model(model_id: str) -> bool:
    lowered = model_id.lower()
    return not any(marker in lowered for marker in _NON_TEXT_MARKERS)


def _classify_entry(entry: Dict[str, Any]) -> Optional[str]:
    """Kind of one OpenAI-style listing entry, preferring the provider's own metadata."""
    model_type = str(entry.get("type") or "").lower()
    if model_type in _EMBEDDING_TYPES:
        return "embedding"
    if model_type and model_type not in _CHAT_TYPES:
        return None  # image, audio, rerank, moderation...
    outputs = (entry.get("architecture") or {}).get("output_modalities")
    if outputs:
        if "embeddings" in outputs:
            return "embedding"
        return "llm" if "text" in outputs and _is_text_model(entry["id"]) else None
    if model_type in _CHAT_TYPES:
        return "llm" if _is_text_model(entry["id"]) else None
    return _classify_by_name(entry["id"])


async def _get_json(
    client: httpx.AsyncClient,
    provider: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    label = provider_label(provider)
    try:
        response = await client.get(url, headers=headers, params=params)
    except httpx.TimeoutException as exc:
        raise DiscoveryError(f"{label} did not answer within {REQUEST_TIMEOUT:.0f}s.", "UNREACHABLE") from exc
    except httpx.HTTPError as exc:
        raise DiscoveryError(f"Couldn't reach {label} at {url}. Check the address and your network.", "UNREACHABLE") from exc
    raise_for_provider_error(provider, response, "listing models")
    try:
        return response.json()
    except ValueError as exc:
        raise DiscoveryError(f"{label} returned something that isn't JSON when listing models.", "BAD_RESPONSE") from exc


def raise_for_provider_error(provider: str, response: httpx.Response, action: str) -> None:
    """Turn a provider's HTTP error into a DiscoveryError a user can act on."""
    if response.status_code < 400:
        return
    label = provider_label(provider)
    detail = error_detail(response)
    # Gemini answers a bad key with 400 "API key not valid", not 401.
    if response.status_code in (401, 403) or "api key" in detail.lower():
        raise DiscoveryError(f"{label} rejected the API key. Check that it is correct and still active.", "AUTH")
    if response.status_code == 429:
        raise DiscoveryError(f"{label} is rate-limiting requests. Wait a minute and try again.", "RATE_LIMITED")
    suffix = f": {detail}" if detail else ""
    raise DiscoveryError(f"{label} returned HTTP {response.status_code} when {action}{suffix}", "BAD_RESPONSE")


def error_detail(response: httpx.Response) -> str:
    """The provider's own error message, when it sends one in the usual shapes."""
    try:
        body = response.json()
    except ValueError:
        return ""
    error = body.get("error") if isinstance(body, dict) else None
    if isinstance(error, dict):
        return str(error.get("message") or "")[:200]
    if isinstance(error, str):
        return error[:200]
    if isinstance(body, dict):
        return str(body.get("message") or body.get("detail") or "")[:200]
    return ""


def _require_key(spec: ProviderSpec, api_key: Optional[str]) -> Optional[str]:
    if spec.list_requires_key and not api_key:
        raise DiscoveryError(f"{spec.label} needs an API key to list its models.", "NO_KEY")
    return api_key


def _bearer(api_key: Optional[str]) -> Optional[Dict[str, str]]:
    return {"Authorization": f"Bearer {api_key}"} if api_key else None


def ollama_base_url(base_url: Optional[str]) -> str:
    return (base_url or os.getenv("OLLAMA_HOST") or "http://localhost:11434").rstrip("/")


def resolved_base_url(spec: ProviderSpec, base_url: Optional[str]) -> str:
    return (base_url or spec.base_url).rstrip("/")


# ---------------------------------------------------------------------------
# Listers, one per wire protocol
# ---------------------------------------------------------------------------

_Lister = Callable[[httpx.AsyncClient, ProviderSpec, Optional[str], Optional[str]], Awaitable[List[DiscoveredModel]]]


def _ollama_model_id(name: str) -> str:
    # Ollama treats "x" and "x:latest" as the same model; datasets and settings
    # store the short form, so the catalogue does too.
    return name[: -len(":latest")] if name.endswith(":latest") else name


async def _list_ollama(client: httpx.AsyncClient, spec: ProviderSpec, api_key: Optional[str], base_url: Optional[str]) -> List[DiscoveredModel]:
    base = ollama_base_url(base_url)
    tags = await _get_json(client, spec.id, f"{base}/api/tags")

    async def describe(entry: Dict[str, Any]) -> Optional[DiscoveredModel]:
        name = entry.get("name") or entry.get("model")
        if not name:
            return None
        try:
            show = (await client.post(f"{base}/api/show", json={"model": name})).json()
        except (httpx.HTTPError, ValueError):
            show = {}
        details = {**(entry.get("details") or {}), **(show.get("details") or {})}
        info = show.get("model_info") or {}
        capabilities = show.get("capabilities") or []

        def info_value(suffix: str) -> Optional[int]:
            if details.get(suffix):
                return int(details[suffix])
            for key, value in info.items():
                if key.endswith(f".{suffix}"):
                    return int(value)
            return None

        if "embedding" in capabilities:
            kind = "embedding"
        elif "completion" in capabilities:
            kind = "llm"
        else:
            # Ollama older than 0.6 reports no capabilities.
            kind = _classify_by_name(name)
            if kind is None:
                return None

        size = entry.get("size")
        return DiscoveredModel(
            model_id=_ollama_model_id(name),
            kind=kind,
            display_name=_ollama_model_id(name),
            description=" · ".join(
                part for part in (
                    details.get("parameter_size"),
                    details.get("quantization_level"),
                    f"{size / 1e9:.1f} GB" if size else None,
                ) if part
            ),
            context_tokens=info_value("context_length"),
            dimension=info_value("embedding_length") if kind == "embedding" else None,
            is_local=True,
            is_free=True,
            metadata={"family": details.get("family"), "capabilities": capabilities},
        )

    described = await asyncio.gather(*(describe(m) for m in tags.get("models", [])))
    return [m for m in described if m]


async def _list_builtin(client: httpx.AsyncClient, spec: ProviderSpec, api_key: Optional[str], base_url: Optional[str]) -> List[DiscoveredModel]:
    """The ONNX models the installed fastembed release can run, with their exact widths."""
    def supported() -> List[Dict[str, Any]]:
        from fastembed import TextEmbedding

        return TextEmbedding.list_supported_models()

    try:
        entries = await asyncio.to_thread(supported)
    except ImportError as exc:
        raise DiscoveryError("Built-in models need the fastembed package, which this image does not include.", "UNSUPPORTED") from exc
    models = []
    for entry in entries:
        size = entry.get("size_in_GB")
        models.append(DiscoveredModel(
            model_id=entry["model"],
            kind="embedding",
            display_name=entry["model"].split("/")[-1],
            description=" · ".join(
                part for part in ((entry.get("description") or "")[:200], f"{size:.2f} GB download" if size else None) if part
            ),
            dimension=int(entry["dim"]) if entry.get("dim") else None,
            is_local=True,
            is_free=True,
            metadata={"license": entry.get("license")},
        ))
    return models


async def _list_gemini(client: httpx.AsyncClient, spec: ProviderSpec, api_key: Optional[str], base_url: Optional[str]) -> List[DiscoveredModel]:
    key = _require_key(spec, api_key)
    models: List[DiscoveredModel] = []
    page_token: Optional[str] = None
    while True:
        params: Dict[str, Any] = {"pageSize": 1000}
        if page_token:
            params["pageToken"] = page_token
        data = await _get_json(client, spec.id, f"{spec.base_url}/models", headers={"x-goog-api-key": key}, params=params)
        for entry in data.get("models", []):
            model_id = entry.get("name", "").removeprefix("models/")
            methods = entry.get("supportedGenerationMethods") or []
            if not model_id:
                continue
            if "embedContent" in methods:
                kind = "embedding"
            elif "generateContent" in methods and _is_text_model(model_id):
                kind = "llm"
            else:
                continue
            models.append(DiscoveredModel(
                model_id=model_id,
                kind=kind,
                display_name=entry.get("displayName") or model_id,
                description=(entry.get("description") or "")[:500],
                context_tokens=entry.get("inputTokenLimit"),
                metadata={"version": entry.get("version"), "output_token_limit": entry.get("outputTokenLimit")},
            ))
        page_token = data.get("nextPageToken")
        if not page_token:
            return models


def _openrouter_entry(entry: Dict[str, Any], kind: str) -> DiscoveredModel:
    pricing = entry.get("pricing") or {}
    prices = [pricing.get(k) for k in ("prompt", "completion") if pricing.get(k) is not None]
    expiration = date.fromisoformat(entry["expiration_date"]) if entry.get("expiration_date") else None
    if expiration and expiration.year > date.today().year + 5:
        expiration = None  # OpenRouter uses far-future dates (2098-12-31) to mean "no end date"
    return DiscoveredModel(
        model_id=entry["id"],
        kind=kind,
        display_name=entry.get("name") or entry["id"],
        description=(entry.get("description") or "")[:500],
        context_tokens=entry.get("context_length"),
        is_free=all(float(p) == 0 for p in prices) if prices else None,
        shutdown_date=expiration,
        metadata={"pricing": pricing, "canonical_slug": entry.get("canonical_slug")},
    )


async def _list_openrouter(client: httpx.AsyncClient, spec: ProviderSpec, api_key: Optional[str], base_url: Optional[str]) -> List[DiscoveredModel]:
    # The listing is public; a key is only needed to generate and embed.
    base = resolved_base_url(spec, None)
    headers = _bearer(api_key)
    if api_key:
        # The listing ignores the key, so check it separately: a typo should
        # surface when the connection is set up, not on the first generation.
        await _get_json(client, spec.id, f"{base}/key", headers=headers)
    chat = await _get_json(client, spec.id, f"{base}/models", headers=headers)
    models = [
        _openrouter_entry(e, "llm")
        for e in chat.get("data", [])
        if e.get("id") and "text" in ((e.get("architecture") or {}).get("output_modalities") or ["text"])
    ]
    try:
        embeddings = await _get_json(client, spec.id, f"{base}/embeddings/models", headers=headers)
        models += [_openrouter_entry(e, "embedding") for e in embeddings.get("data", []) if e.get("id")]
    except DiscoveryError as exc:
        # Chat models are the core listing; a missing embeddings listing must
        # not fail the whole sync (that would freeze lifecycle for chat models).
        logger.warning(f"OpenRouter embeddings listing unavailable: {exc.message}")
    return models


async def _list_openai_compatible(client: httpx.AsyncClient, spec: ProviderSpec, api_key: Optional[str], base_url: Optional[str]) -> List[DiscoveredModel]:
    if spec.id == "openrouter":
        return await _list_openrouter(client, spec, api_key, base_url)
    base = resolved_base_url(spec, base_url)
    if not base:
        raise DiscoveryError(f"{spec.label} needs a server URL before its models can be listed.", "NO_KEY")
    _require_key(spec, api_key)
    data = await _get_json(client, spec.id, f"{base}/models", headers=_bearer(api_key))
    entries = data if isinstance(data, list) else data.get("data", [])  # Together returns a bare list
    models: List[DiscoveredModel] = []
    for entry in entries:
        model_id = entry.get("id") if isinstance(entry, dict) else None
        if not model_id or entry.get("active") is False:
            continue
        kind = _classify_entry(entry)
        if kind is None:
            continue
        owner = entry.get("owned_by") or entry.get("organization")
        models.append(DiscoveredModel(
            model_id=model_id,
            kind=kind,
            display_name=entry.get("display_name") or entry.get("name") or model_id,
            description=f"by {owner}" if owner else "",
            context_tokens=entry.get("context_window") or entry.get("context_length"),
            metadata={"owned_by": owner},
        ))
    return models


async def _list_anthropic(client: httpx.AsyncClient, spec: ProviderSpec, api_key: Optional[str], base_url: Optional[str]) -> List[DiscoveredModel]:
    key = _require_key(spec, api_key)
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    models: List[DiscoveredModel] = []
    params: Dict[str, Any] = {"limit": 1000}
    while True:
        data = await _get_json(client, spec.id, f"{spec.base_url}/models", headers=headers, params=params)
        for entry in data.get("data", []):
            if entry.get("id"):
                models.append(DiscoveredModel(
                    model_id=entry["id"], kind="llm", display_name=entry.get("display_name") or entry["id"],
                ))
        if not data.get("has_more"):
            return models
        params["after_id"] = data.get("last_id")


async def _list_huggingface(client: httpx.AsyncClient, spec: ProviderSpec, api_key: Optional[str], base_url: Optional[str]) -> List[DiscoveredModel]:
    # The Hub hosts millions of models; list the ones an inference provider
    # is actually serving, most downloaded first.
    models: List[DiscoveredModel] = []
    for tag, kind in (("text-generation", "llm"), ("feature-extraction", "embedding")):
        data = await _get_json(
            client, spec.id, f"{HUGGINGFACE_HUB_URL}/models", headers=_bearer(api_key),
            params={"pipeline_tag": tag, "inference_provider": "all", "sort": "downloads", "limit": 100},
        )
        models += [
            DiscoveredModel(model_id=e["id"], kind=kind, display_name=e["id"])
            for e in data if isinstance(e, dict) and e.get("id")
        ]
    return models


_LISTERS: Dict[str, _Lister] = {
    registry.OLLAMA: _list_ollama,
    registry.BUILTIN: _list_builtin,
    registry.GEMINI: _list_gemini,
    registry.OPENAI: _list_openai_compatible,
    registry.XAI: _list_openai_compatible,
    registry.CUSTOM: _list_openai_compatible,
    registry.ANTHROPIC: _list_anthropic,
    registry.HUGGINGFACE: _list_huggingface,
}

SUPPORTED_PROVIDERS = tuple(p.id for p in registry.PROVIDERS)


def check_base_url(provider: str, base_url: Optional[str]) -> Optional[str]:
    """
    Hosted providers always use their public endpoint; only self-hosted ones
    take a user-supplied URL. Private addresses stay allowed (a local model
    server is the point of "custom"), but link-local ones never are: that range
    holds cloud metadata services, which the server must not be made to call.
    """
    spec = registry.get_provider(provider)
    if not base_url or spec is None or not spec.custom_base_url:
        return None
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise DiscoveryError("The server URL must start with http:// or https://.", "BAD_RESPONSE")
    try:
        address = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
    except (socket.gaierror, ValueError) as exc:
        raise DiscoveryError(f"Couldn't resolve the host '{parsed.hostname}'.", "UNREACHABLE") from exc
    if address.is_link_local or address.is_multicast or address.is_unspecified:
        raise DiscoveryError("That address is not allowed as a model endpoint.", "UNREACHABLE")
    return base_url


# Kept for callers and tests that use the original name.
_check_base_url = check_base_url


async def discover_models(provider: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> List[DiscoveredModel]:
    """List the models `provider` serves for this credential. Raises DiscoveryError."""
    spec = registry.get_provider(provider)
    if spec is None:
        raise DiscoveryError(f"Listing models is not supported for '{provider}'.", "UNSUPPORTED")
    base_url = await asyncio.to_thread(check_base_url, provider, base_url)
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        models = await _LISTERS[spec.api](client, spec, api_key, base_url)
    # A provider listing the same id twice (OpenRouter chat + embeddings) keeps the first.
    unique: Dict[str, DiscoveredModel] = {}
    for model in models:
        unique.setdefault(model.model_id, model)
    return list(unique.values())


async def probe_dimension(provider: str, model_id: str, api_key: Optional[str], base_url: Optional[str] = None) -> Optional[int]:
    """
    Measure an embedding model's output width by embedding one short string.

    Returns None when it cannot be measured (no key, provider error). The
    catalogue then shows the dimension as unknown rather than inventing one.
    """
    from app.llm.embeddings import EmbeddingError, embed_texts

    try:
        vectors = await embed_texts(provider, model_id, ["dimension probe"], api_key=api_key, base_url=base_url)
    except EmbeddingError as exc:
        logger.warning(f"Could not measure dimension of {provider}/{model_id}: {exc.message}")
        return None
    return len(vectors[0]) if vectors and vectors[0] else None
