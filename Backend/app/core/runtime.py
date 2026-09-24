"""
Deployment runtime
==================

One codebase, two deployment shapes, selected by `EXECUTION_MODE`.

    local   Zero-cost, fully offline. Ollama in a container supplies both
            embeddings and generation. No API keys, nothing leaves the machine.

    cloud   Deployable for a few dollars a month. Embeddings run IN-PROCESS via
            ONNX (the "builtin" provider); generation goes to a hosted API.

WHAT THIS MODULE DECIDES -- AND WHAT IT NO LONGER DOES
----------------------------------------------------
Each user picks their own embedding model (Settings -> Embedding model), from
any provider in `app.llm.provider_registry`. This module only supplies the
DEPLOYMENT DEFAULT: the model used for the demo tenant and for any user who has
not chosen one. Override it with EMBEDDING_PROVIDER / EMBEDDING_MODEL; otherwise
it follows EXECUTION_MODE:

    local  -> ollama  / OLLAMA_EMBED_MODEL (nomic-embed-text)
    cloud  -> builtin / ONNX_EMBED_MODEL   (BAAI/bge-small-en-v1.5)

DIMENSION IS MEASURED, NOT DECLARED
-----------------------------------
Vectors are only comparable within one (provider, model, dimension). The
embedder starts from a dimension hint and replaces it with the width of the
first vector it actually produces, so a misconfigured hint cannot index
vectors under the wrong dimension.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Protocol, Sequence, runtime_checkable

from app.core.logger import logger

EXECUTION_MODE = os.getenv("EXECUTION_MODE", "local").lower()

OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_EMBED_DIM = int(os.getenv("OLLAMA_EMBED_DIM", "768"))
ONNX_EMBED_MODEL = os.getenv("ONNX_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
ONNX_EMBED_DIM = int(os.getenv("ONNX_EMBED_DIM", "384"))


@runtime_checkable
class Embedder(Protocol):
    """Minimal contract the retrieval pipeline depends on."""

    provider: str
    model_id: str
    dimension: int

    async def embed(self, texts: Sequence[str]) -> List[List[float]]: ...
    async def embed_one(self, text: str) -> List[float]: ...
    async def health(self) -> bool: ...


class ProviderEmbedder:
    """An Embedder bound to one (provider, model, credential)."""

    def __init__(
        self,
        provider: str,
        model_id: str,
        dimension: Optional[int] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.provider = provider
        self.model_id = model_id
        self.dimension = dimension or 0
        self._api_key = api_key
        self._base_url = base_url

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        from app.llm.embeddings import embed_texts

        vectors = await embed_texts(
            self.provider, self.model_id, list(texts), api_key=self._api_key, base_url=self._base_url
        )
        measured = len(vectors[0])
        if measured != self.dimension:
            if self.dimension:
                logger.warning(
                    f"{self.provider}/{self.model_id} produces {measured}-dim vectors, "
                    f"not the configured {self.dimension}; using {measured}"
                )
            self.dimension = measured
        return vectors

    async def embed_one(self, text: str) -> List[float]:
        out = await self.embed([text])
        return out[0] if out else []

    async def warm(self) -> bool:
        return await self.health()

    async def health(self) -> bool:
        try:
            return bool(await self.embed_one("health check"))
        except Exception as exc:  # noqa: BLE001 - health reports, never raises
            logger.warning(f"Embedder {self.provider}/{self.model_id} unavailable: {exc}")
            return False


def default_embedding() -> Dict[str, Any]:
    """The deployment default (provider, model, dimension hint)."""
    if EXECUTION_MODE not in ("local", "cloud"):
        raise ValueError(f"EXECUTION_MODE must be 'local' or 'cloud', got {EXECUTION_MODE!r}")
    cloud = EXECUTION_MODE == "cloud"
    provider = os.getenv("EMBEDDING_PROVIDER") or ("builtin" if cloud else "ollama")
    model = os.getenv("EMBEDDING_MODEL") or (ONNX_EMBED_MODEL if cloud else OLLAMA_EMBED_MODEL)
    hint = int(os.getenv("EMBEDDING_DIM", "0")) or (ONNX_EMBED_DIM if cloud else OLLAMA_EMBED_DIM)
    return {"provider": provider, "model_id": model, "dimension": hint}


_embedder: Optional[ProviderEmbedder] = None


def get_embedder() -> ProviderEmbedder:
    """The deployment-default embedder. Process-wide singleton."""
    global _embedder
    if _embedder is not None:
        return _embedder
    default = default_embedding()
    from app.llm.provider_registry import get_provider

    spec = get_provider(default["provider"])
    api_key = os.getenv(spec.env_key) if spec and spec.env_key else None
    _embedder = ProviderEmbedder(default["provider"], default["model_id"], default["dimension"], api_key=api_key)
    logger.info(
        f"Runtime: EXECUTION_MODE={EXECUTION_MODE} default embedder="
        f"{_embedder.provider}/{_embedder.model_id} (~{_embedder.dimension}-dim)"
    )
    return _embedder


def reset_embedder() -> None:
    """Drop the cached embedder. Tests only."""
    global _embedder
    _embedder = None


def runtime_info() -> Dict[str, Any]:
    """Surfaced on /health so the deployed mode is never in doubt."""
    emb = get_embedder()
    return {
        "execution_mode": EXECUTION_MODE,
        "embedder": {"provider": emb.provider, "model": emb.model_id, "dimension": emb.dimension},
        "embedding_model_per_user": True,
        "generation": "ollama" if EXECUTION_MODE == "local" else "hosted-api",
        "extraction_model": os.getenv("EXTRACTION_MODEL", "llama3.2:3b"),
        "reranker_enabled": os.getenv("RERANKER_ENABLED", "false").lower() in ("1", "true", "yes"),
        "stage1_top_k": int(os.getenv("STAGE1_TOP_K", "25")),
        "vector_backend": "pgvector",
        # Vectors are only comparable within one (provider, model, dimension).
        "reembed_required_on_model_switch": True,
    }
