"""Embedding clients and the provider registry (HTTP served by an in-memory transport)."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.llm import embeddings, provider_registry
from app.llm.embeddings import EmbeddingError, embed_texts


def _serve(handler):
    """Make embed_texts' AsyncClient talk to `handler` instead of the network."""
    real = httpx.AsyncClient

    def factory(*args, **kwargs):
        return real(*args, transport=httpx.MockTransport(handler), **kwargs)

    return patch.object(embeddings.httpx, "AsyncClient", factory)


@pytest.mark.asyncio
async def test_openai_compatible_payload_and_order():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        # Out of order on purpose: results must be re-sorted by index.
        return httpx.Response(200, json={"data": [
            {"index": 1, "embedding": [0.0, 1.0]},
            {"index": 0, "embedding": [1.0, 0.0]},
        ]})

    with _serve(handler):
        vectors = await embed_texts("nvidia", "nvidia/nv-embedqa-e5-v5", ["a", "b"], api_key="k")

    assert seen["url"] == "https://integrate.api.nvidia.com/v1/embeddings"
    assert seen["auth"] == "Bearer k"
    # Provider-specific fields from the registry are sent.
    assert seen["body"]["input_type"] == "query"
    assert vectors == [[1.0, 0.0], [0.0, 1.0]]


@pytest.mark.asyncio
async def test_rate_limit_is_retried_after_the_advertised_delay():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"retry-after": "2"}, json={"error": {"message": "slow down"}})
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": [0.5]}]})

    sleep = AsyncMock()
    with _serve(handler), patch.object(embeddings.asyncio, "sleep", sleep):
        vectors = await embed_texts("mistral", "mistral-embed", ["x"], api_key="k")

    assert vectors == [[0.5]]
    sleep.assert_awaited_once_with(2.0)


@pytest.mark.asyncio
async def test_persistent_rate_limit_explains_the_free_tier():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "quota"}})

    with _serve(handler), patch.object(embeddings.asyncio, "sleep", AsyncMock()), \
            patch.object(embeddings, "MAX_RETRIES", 2):
        with pytest.raises(EmbeddingError) as err:
            await embed_texts("google", "gemini-embedding-001", ["x"], api_key="k")

    assert err.value.code == "RATE_LIMITED"
    assert "Free tiers" in err.value.message


@pytest.mark.asyncio
async def test_rejected_key_says_where_to_fix_it():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "invalid key"}})

    with _serve(handler):
        with pytest.raises(EmbeddingError) as err:
            await embed_texts("openai", "text-embedding-3-small", ["x"], api_key="bad")

    assert err.value.code == "AUTH"
    assert "Settings → AI Providers" in err.value.message


@pytest.mark.asyncio
async def test_keyed_provider_without_key_is_refused_before_any_call():
    with pytest.raises(EmbeddingError) as err:
        await embed_texts("openai", "text-embedding-3-small", ["x"])
    assert err.value.code == "NO_KEY"


@pytest.mark.asyncio
async def test_chat_only_provider_has_no_embeddings():
    with pytest.raises(EmbeddingError) as err:
        await embed_texts("anthropic", "claude-x", ["x"], api_key="k")
    assert err.value.code == "UNSUPPORTED"


@pytest.mark.asyncio
async def test_gemini_batches_through_batch_embed_contents():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("x-goog-api-key")
        body = json.loads(request.content)
        return httpx.Response(200, json={"embeddings": [{"values": [0.1, 0.2]} for _ in body["requests"]]})

    with _serve(handler):
        vectors = await embed_texts("google", "gemini-embedding-001", ["a", "b", "c"], api_key="g")

    assert seen["url"].endswith("/models/gemini-embedding-001:batchEmbedContents")
    assert seen["key"] == "g"
    assert len(vectors) == 3


def test_registry_is_consistent():
    ids = [p.id for p in provider_registry.PROVIDERS]
    assert len(ids) == len(set(ids))
    for spec in provider_registry.PROVIDERS:
        assert spec.api in embeddings._EMBEDDERS or not spec.embeddings, spec.id
        if spec.api == provider_registry.OPENAI:
            assert spec.base_url.startswith("https://"), spec.id
        if spec.requires_key:
            assert spec.env_key, f"{spec.id} needs an env var so a deployment can share one key"
