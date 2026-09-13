"""
Dual-Runtime Adapter
====================

One codebase, two deployment shapes, selected by `EXECUTION_MODE`.

    local   Zero-cost, fully offline. Ollama in a container supplies both
            embeddings and generation. No API keys, nothing leaves the machine.
            This is the `docker compose up` story and a genuine selling point.

    cloud   Deployable for a few dollars a month. Embeddings run IN-PROCESS via
            ONNX (bge-small-en-v1.5, 384-dim, ~130MB); generation goes to a
            hosted API (Gemini Flash / Groq / OpenRouter).

WHY THE CLOUD MODE EXISTS
-------------------------
Ollama is the reason v1 could not be deployed. It wants 4-8GB of RAM and
realistically a GPU; no free tier will host it, and a VM that runs it costs more
than every other component combined. Every "I'll deploy it later" plan for this
project died on that constraint.

Running a small ONNX embedder inside the FastAPI process removes the dependency
entirely: no model server, no GPU, ~130MB resident. The whole system collapses to
FastAPI + Postgres, which fits anywhere.

WHY ONNX AND NOT A HOSTED EMBEDDING API
---------------------------------------
Embeddings are called on every query AND on every generated dataset row -- easily
thousands of calls per dataset. A hosted embedding API turns that into per-row
cost and per-row latency. bge-small runs locally in single-digit milliseconds at
zero marginal cost. Generation is the opposite: called once per request, benefits
from a large model, so it goes hosted.

DIMENSION IS PART OF THE CONTRACT
---------------------------------
Local (nomic-embed-text) is 768-dim; cloud (bge-small) is 384-dim. Vectors
embedded in one mode are meaningless in the other -- so `vector_rows` records
both model and dimension per row, and Stage 1 filters on them. Switching modes
requires a re-embed, and the compatibility check will say so rather than silently
returning garbage distances.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional, Protocol, Sequence, runtime_checkable

from app.core.logger import logger

EXECUTION_MODE = os.getenv("EXECUTION_MODE", "local").lower()

# -- local mode ------------------------------------------------------------
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_EMBED_DIM = int(os.getenv("OLLAMA_EMBED_DIM", "768"))

# -- cloud mode ------------------------------------------------------------
ONNX_EMBED_MODEL = os.getenv("ONNX_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
ONNX_EMBED_DIM = int(os.getenv("ONNX_EMBED_DIM", "384"))
# Baked into the image at build time so cold start never downloads a model.
ONNX_CACHE_DIR = os.getenv("ONNX_CACHE_DIR", "/opt/models/fastembed")


@runtime_checkable
class Embedder(Protocol):
    """Minimal contract the retrieval pipeline depends on."""

    model_id: str
    dimension: int

    async def embed(self, texts: Sequence[str]) -> List[List[float]]: ...
    async def embed_one(self, text: str) -> List[float]: ...
    async def health(self) -> bool: ...


# ---------------------------------------------------------------------------
# Cloud: in-process ONNX
# ---------------------------------------------------------------------------

class OnnxEmbedder:
    """
    bge-small-en-v1.5 through fastembed's ONNX runtime.

    Loads lazily behind a lock and runs inference in a worker thread -- ONNX is
    CPU-bound and would otherwise stall the event loop for the duration of every
    embed call, which is exactly the bug Phase 1 fixed for Redis.
    """

    def __init__(
        self,
        model_id: str = ONNX_EMBED_MODEL,
        dimension: int = ONNX_EMBED_DIM,
        cache_dir: str = ONNX_CACHE_DIR,
    ) -> None:
        self.model_id = model_id
        self.dimension = dimension
        self.cache_dir = cache_dir
        self._model: Any = None
        self._lock = asyncio.Lock()

    def _load_sync(self) -> Any:
        from fastembed import TextEmbedding

        os.makedirs(self.cache_dir, exist_ok=True)
        model = TextEmbedding(model_name=self.model_id, cache_dir=self.cache_dir)
        logger.info(f"ONNX embedder loaded: {self.model_id} ({self.dimension}-dim)")
        return model

    async def _ensure(self) -> Any:
        if self._model is not None:
            return self._model
        async with self._lock:
            if self._model is None:
                self._model = await asyncio.to_thread(self._load_sync)
        return self._model

    async def warm(self) -> bool:
        try:
            await self._ensure()
            await self.embed_one("warmup")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(f"ONNX embedder warmup failed: {exc}")
            return False

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        model = await self._ensure()

        def _run() -> List[List[float]]:
            return [v.tolist() for v in model.embed(list(texts))]

        return await asyncio.to_thread(_run)

    async def embed_one(self, text: str) -> List[float]:
        out = await self.embed([text])
        return out[0] if out else []

    async def health(self) -> bool:
        return self._model is not None or await self.warm()


# ---------------------------------------------------------------------------
# Local: Ollama
# ---------------------------------------------------------------------------

class OllamaEmbedderAdapter:
    """Wraps the existing Ollama service in the Embedder protocol."""

    def __init__(
        self, model_id: str = OLLAMA_EMBED_MODEL, dimension: int = OLLAMA_EMBED_DIM
    ) -> None:
        self.model_id = model_id
        self.dimension = dimension
        from app.services.ollama_embedding_service import get_ollama_service

        self._svc = get_ollama_service()

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        out = await self._svc.generate_embeddings_batch(self.model_id, list(texts))
        return [v for v in out if v]

    async def embed_one(self, text: str) -> List[float]:
        return await self._svc.generate_embedding(self.model_id, text) or []

    async def health(self) -> bool:
        try:
            return await self._svc.check_ollama_available()
        except Exception:  # noqa: BLE001
            return False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_embedder: Optional[Embedder] = None


def get_embedder() -> Embedder:
    """The embedder for the active EXECUTION_MODE. Process-wide singleton."""
    global _embedder
    if _embedder is not None:
        return _embedder

    if EXECUTION_MODE == "cloud":
        _embedder = OnnxEmbedder()
    elif EXECUTION_MODE == "local":
        _embedder = OllamaEmbedderAdapter()
    else:
        raise ValueError(
            f"EXECUTION_MODE must be 'local' or 'cloud', got {EXECUTION_MODE!r}"
        )

    logger.info(
        f"Runtime: EXECUTION_MODE={EXECUTION_MODE} "
        f"embedder={_embedder.model_id} dim={_embedder.dimension}"
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
        "embedder": {"model": emb.model_id, "dimension": emb.dimension},
        "generation": "ollama" if EXECUTION_MODE == "local" else "hosted-api",
        "vector_backend": os.getenv("VECTOR_BACKEND", "pgvector"),
        # Vectors are only comparable within one (model, dimension) pair.
        "reembed_required_on_mode_switch": True,
    }
