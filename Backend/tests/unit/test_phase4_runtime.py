"""
Phase 4 unit tests — dual-runtime adapter.

The failure this guards against is a mode switch that silently produces
incomparable vectors: 768-dim rows written in local mode, then queried with a
384-dim cloud embedder. Distances would still compute; they would just be
meaningless.
"""

from __future__ import annotations

import importlib
import os
from typing import List, Sequence

import pytest


def _reload_runtime(mode: str):
    """Re-import app.core.runtime with EXECUTION_MODE bound at module level."""
    os.environ["EXECUTION_MODE"] = mode
    import app.core.runtime as rt

    importlib.reload(rt)
    rt.reset_embedder()
    return rt


@pytest.fixture(autouse=True)
def _restore_mode():
    before = os.environ.get("EXECUTION_MODE")
    yield
    if before is None:
        os.environ.pop("EXECUTION_MODE", None)
    else:
        os.environ["EXECUTION_MODE"] = before
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


def test_cloud_mode_selects_onnx_embedder():
    rt = _reload_runtime("cloud")
    emb = rt.get_embedder()
    assert type(emb).__name__ == "OnnxEmbedder"
    assert emb.dimension == 384
    assert "bge-small" in emb.model_id


def test_local_and_cloud_dimensions_differ():
    """
    Documents the contract: switching modes invalidates existing vectors.
    If these ever match by accident, the re-embed warning becomes wrong.
    """
    cloud = _reload_runtime("cloud").get_embedder()
    cloud_dim, cloud_model = cloud.dimension, cloud.model_id

    rt = _reload_runtime("local")
    local_dim = rt.OLLAMA_EMBED_DIM
    local_model = rt.OLLAMA_EMBED_MODEL

    assert cloud_dim != local_dim, (
        "local and cloud embedders share a dimension; a mode switch would "
        "silently mix incomparable vectors instead of failing the compat check"
    )
    assert cloud_model != local_model


def test_runtime_info_reports_mode_and_reembed_requirement():
    rt = _reload_runtime("cloud")
    info = rt.runtime_info()

    assert info["execution_mode"] == "cloud"
    assert info["embedder"]["dimension"] == 384
    assert info["generation"] == "hosted-api"
    assert info["reembed_required_on_mode_switch"] is True


def test_embedder_is_a_singleton():
    rt = _reload_runtime("cloud")
    assert rt.get_embedder() is rt.get_embedder()


@pytest.mark.asyncio
async def test_onnx_embedder_offloads_to_thread():
    """
    ONNX inference is CPU-bound. Running it on the event loop would reintroduce
    exactly the stall Phase 1 removed from the Redis path, so embed() must not
    block — verified by racing it against a timer coroutine.
    """
    import asyncio

    rt = _reload_runtime("cloud")
    emb = rt.OnnxEmbedder()

    class _SlowModel:
        def embed(self, texts: Sequence[str]) -> List[Any]:  # type: ignore[name-defined]
            import time

            time.sleep(0.15)  # blocking, as real ONNX inference is
            return [_Vec([0.1] * 384) for _ in texts]

    class _Vec:
        def __init__(self, v):
            self._v = v

        def tolist(self):
            return self._v

    emb._model = _SlowModel()

    ticks = 0

    async def ticker():
        nonlocal ticks
        for _ in range(10):
            await asyncio.sleep(0.01)
            ticks += 1

    await asyncio.gather(emb.embed(["a", "b"]), ticker())

    assert ticks >= 5, (
        f"event loop was blocked during embedding (only {ticks} ticks); "
        f"embed() must dispatch via asyncio.to_thread"
    )


def test_seed_demo_and_benchmark_share_one_catalogue():
    """
    The demo tenant is seeded from evals/api_surface.py on purpose: the numbers
    in the README must be reproducible against what a reviewer clicks. Two
    fixtures would drift.
    """
    import sys
    from pathlib import Path

    evals_dir = Path(__file__).resolve().parents[3] / "evals"
    sys.path.insert(0, str(evals_dir))
    from api_surface import API_TEMPLATES  # type: ignore[import-not-found]

    seed_src = (
        Path(__file__).resolve().parents[2] / "scripts" / "seed_demo.py"
    ).read_text(encoding="utf-8")

    assert "from api_surface import API_TEMPLATES" in seed_src
    assert len(API_TEMPLATES) == 20
    assert all(t.get("utterances") for t in API_TEMPLATES)
