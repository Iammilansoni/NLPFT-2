"""
Runtime unit tests — the deployment-default embedding model.

Users pick their own embedding model; the runtime only supplies the default
(used for the demo tenant and anyone who has not chosen). The failure these
guard against is vectors indexed under the wrong (provider, model, dimension):
distances would still compute, they would just be meaningless.
"""

from __future__ import annotations

import importlib
import os
from typing import Any, List, Sequence
from unittest.mock import AsyncMock, patch

import pytest

_ENV = ("EXECUTION_MODE", "EMBEDDING_PROVIDER", "EMBEDDING_MODEL", "EMBEDDING_DIM")


def _reload_runtime(mode: str, **env: str):
    """Re-import app.core.runtime with EXECUTION_MODE bound at module level."""
    os.environ["EXECUTION_MODE"] = mode
    for key, value in env.items():
        os.environ[key] = value
    import app.core.runtime as rt

    importlib.reload(rt)
    rt.reset_embedder()
    return rt


@pytest.fixture(autouse=True)
def _restore_env():
    before = {k: os.environ.get(k) for k in _ENV}
    yield
    for key, value in before.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    import app.core.runtime as rt

    importlib.reload(rt)
    rt.reset_embedder()


def test_invalid_execution_mode_fails_loudly():
    """
    A typo'd mode must not silently fall back to a default. Falling back would
    embed with the wrong model and corrupt the index.
    """
    rt = _reload_runtime("clould")
    with pytest.raises(ValueError, match="local.*cloud"):
        rt.get_embedder()


def test_cloud_default_is_the_in_process_onnx_model():
    emb = _reload_runtime("cloud").get_embedder()
    assert emb.provider == "builtin"
    assert "bge-small" in emb.model_id
    assert emb.dimension == 384


def test_local_default_is_ollama():
    emb = _reload_runtime("local").get_embedder()
    assert emb.provider == "ollama"
    assert emb.model_id == "nomic-embed-text"


def test_default_can_be_any_registry_provider():
    emb = _reload_runtime(
        "local", EMBEDDING_PROVIDER="mistral", EMBEDDING_MODEL="mistral-embed", EMBEDDING_DIM="1024"
    ).get_embedder()
    assert (emb.provider, emb.model_id, emb.dimension) == ("mistral", "mistral-embed", 1024)


def test_runtime_info_reports_the_default_and_per_user_models():
    info = _reload_runtime("cloud").runtime_info()

    assert info["execution_mode"] == "cloud"
    assert info["embedder"]["provider"] == "builtin"
    assert info["embedding_model_per_user"] is True
    assert info["reembed_required_on_model_switch"] is True


def test_embedder_is_a_singleton():
    rt = _reload_runtime("cloud")
    assert rt.get_embedder() is rt.get_embedder()


@pytest.mark.asyncio
async def test_dimension_is_measured_not_trusted():
    """A wrong dimension hint must be replaced by the width the model really produces."""
    rt = _reload_runtime("local", EMBEDDING_DIM="1234")
    emb = rt.get_embedder()
    assert emb.dimension == 1234

    with patch("app.llm.embeddings.embed_texts", AsyncMock(return_value=[[0.1] * 768])):
        await emb.embed(["hello"])

    assert emb.dimension == 768


@pytest.mark.asyncio
async def test_builtin_embedding_offloads_to_thread():
    """
    ONNX inference is CPU-bound. Running it on the event loop would stall every
    other request, so the built-in client must dispatch it to a thread --
    verified by racing it against a timer coroutine.
    """
    import asyncio

    from app.llm import embeddings

    class _Vec:
        def __init__(self, v):
            self._v = v

        def tolist(self):
            return self._v

    class _SlowModel:
        def embed(self, texts: Sequence[str]) -> List[Any]:
            import time

            time.sleep(0.15)  # blocking, as real ONNX inference is
            return [_Vec([0.1] * 384) for _ in texts]

    embeddings._BUILTIN_MODELS["slow-test-model"] = _SlowModel()
    ticks = 0

    async def ticker():
        nonlocal ticks
        for _ in range(10):
            await asyncio.sleep(0.01)
            ticks += 1

    try:
        await asyncio.gather(embeddings.embed_texts("builtin", "slow-test-model", ["a", "b"]), ticker())
    finally:
        embeddings._BUILTIN_MODELS.pop("slow-test-model", None)

    assert ticks >= 5, (
        f"event loop was blocked during embedding (only {ticks} ticks); "
        f"the built-in client must dispatch via asyncio.to_thread"
    )


def test_seed_demo_and_benchmark_share_one_catalogue():
    """
    The demo tenant and the routing benchmark read ONE catalogue on purpose: the
    numbers in the README must be reproducible against what a reviewer clicks.
    Two fixtures would drift.
    """
    from pathlib import Path

    from app.demo_catalogue import API_TEMPLATES

    root = Path(__file__).resolve().parents[3]
    seed_src = (root / "Backend" / "scripts" / "seed_demo.py").read_text(encoding="utf-8")
    evals_src = (root / "evals" / "api_surface.py").read_text(encoding="utf-8")

    assert "from app.demo_catalogue import API_TEMPLATES" in seed_src
    assert "from app.demo_catalogue import" in evals_src
    assert len(API_TEMPLATES) == 20
    assert all(t.get("utterances") for t in API_TEMPLATES)
