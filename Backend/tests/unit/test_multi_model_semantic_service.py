"""Unit tests for the routing pipeline orchestration (all I/O mocked)."""

import uuid
from contextlib import ExitStack, asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas.embedding_schemas import ErrorCode
from app.services.model_access import EmbeddingSelection
from app.services.multi_model_semantic_service import MultiModelSemanticRetrievalService
from app.services.structured_extraction_service import ExtractionResult

T1 = "00000000-0000-0000-0000-000000000001"
T2 = "00000000-0000-0000-0000-000000000002"
MODULE = "app.services.multi_model_semantic_service"

# The embedding model is per user; this is the one the test user searches with.
ACTIVE = EmbeddingSelection("ollama", "test-model-1", 768, is_default=False)


def _group(provider, model, dim, names):
    return {
        "provider": provider, "provider_label": provider.title(), "model_id": model, "dimension": dim,
        "label": f"{provider} · {model} · {dim}-dim",
        "datasets": [{"dataset_id": str(uuid.uuid4()), "name": n, "rows": 10} for n in names],
    }


@pytest.fixture
def mock_embedder():
    embedder = AsyncMock()
    embedder.embed_one.return_value = [0.1] * 768
    return embedder


@pytest.fixture
def mock_pgvector_store():
    store = AsyncMock()
    result = MagicMock()
    result.latency_ms = 1.0
    result.rows = [
        {"row_uid": "r1", "t_id": T1, "template_id": T1, "similarity": 0.95,
         "query": "test query", "api_name": "Test API"},
        {"row_uid": "r2", "t_id": T2, "template_id": T2, "similarity": 0.85,
         "query": "another query", "api_name": "Other API"},
    ]
    store.search.return_value = result
    return store


@pytest.fixture
def mock_extractor():
    # Stage 3 is the schema-constrained StructuredExtractionService.
    service = AsyncMock()
    service.extract.return_value = ExtractionResult(ok=True, values={"account_id": "12345"})
    return service


@pytest.fixture
def groups():
    """Embedded datasets grouped by model; tests append groups from other models."""
    return [_group("ollama", "test-model-1", 768, ["Orders"])]


@pytest.fixture
def semantic_service(mock_embedder, mock_pgvector_store, mock_extractor, groups):
    @asynccontextmanager
    async def _fake_tenant_session(user_id):
        yield AsyncMock()

    # tenant_session is entered inside semantic_search() on every call, so the
    # patch must stay active for the whole test, not just construction. Letting
    # the real one run would try set_config() against CI's SQLite.
    with ExitStack() as stack:
        stack.enter_context(patch(f"{MODULE}.active_embedding", AsyncMock(return_value=ACTIVE)))
        stack.enter_context(patch(f"{MODULE}.embedder_for", AsyncMock(return_value=mock_embedder)))
        stack.enter_context(patch(f"{MODULE}.embedding_groups", AsyncMock(return_value=groups)))
        stack.enter_context(
            patch(f"{MODULE}.get_pgvector_store", return_value=mock_pgvector_store)
        )
        stack.enter_context(patch(f"{MODULE}.tenant_session", _fake_tenant_session))
        stack.enter_context(
            patch(f"{MODULE}.get_structured_extraction_service", return_value=mock_extractor)
        )
        yield MultiModelSemanticRetrievalService()


def _template(name="Test API"):
    t = MagicMock()
    t.api_name = name
    t.endpoint = "/api/test"
    t.method = "POST"
    t.base_url = "https://api.example.com"
    t.json_schema = {"type": "object", "properties": {"account_id": {"type": "string"}}}
    t.domain_tags = []
    return t


def _dataset(provider="ollama", model="test-model-1", dim=768):
    return MagicMock(
        dataset_id=uuid.uuid4(), embedding_provider=provider, embedding_model=model, embedding_dimension=dim
    )


@pytest.mark.asyncio
async def test_semantic_search_success_flow(
    semantic_service, mock_pgvector_store, mock_extractor
):
    db = AsyncMock()
    db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: _dataset()),
        MagicMock(scalar_one_or_none=lambda: _template()),
    ]

    result = await semantic_service.semantic_search(
        db=db, user_id=uuid.uuid4(), user_query="Find user by account id 12345",
        top_k=5, dataset_id=uuid.uuid4(),
    )

    assert result["success"] is True
    # Max-pool: the template of the best-scoring row wins.
    assert result["final_output"]["t_id"] == T1
    assert result["extracted_request_body"] == {"account_id": "12345"}
    assert result["extraction"]["ok"] is True
    # Reranker off by configuration is the measured default, not degradation.
    assert result["ranking"]["strategy"] == "vector_maxpool"
    assert result["degraded"] is False
    # Stage 1 searches only vectors from the user's own model.
    kwargs = mock_pgvector_store.search.call_args.kwargs
    assert (kwargs["embedding_provider"], kwargs["embedding_model"], kwargs["dimension"]) == ("ollama", "test-model-1", 768)
    assert result["metadata"]["excluded_datasets"] == []
    assert result["options"] is None
    mock_extractor.extract.assert_called_once()


@pytest.mark.asyncio
async def test_extraction_failure_is_reported_as_degraded(semantic_service, mock_extractor):
    db = AsyncMock()
    db.execute.side_effect = [MagicMock(scalar_one_or_none=lambda: _template())]
    mock_extractor.extract.return_value = ExtractionResult(
        ok=False, degraded=True, reason="llm_unreachable (ConnectError)"
    )

    result = await semantic_service.semantic_search(
        db=db, user_id=uuid.uuid4(), user_query="Test query"
    )

    # Routing still answers; the caller is told extraction did not run.
    assert result["success"] is True
    assert result["degraded"] is True
    assert result["extraction"]["reason"].startswith("llm_unreachable")


@pytest.mark.asyncio
async def test_dataset_from_another_model_offers_switch_or_reembed(semantic_service, mock_pgvector_store):
    dataset = _dataset("google", "gemini-embedding-001", 3072)
    db = AsyncMock()
    db.execute.side_effect = [MagicMock(scalar_one_or_none=lambda: dataset)]

    result = await semantic_service.semantic_search(
        db=db, user_id=uuid.uuid4(), user_query="Test query", dataset_id=dataset.dataset_id
    )

    assert result["success"] is False
    assert result["error"] == ErrorCode.MODEL_MISMATCH
    actions = {o["action"]: o for o in result["options"]}
    assert actions["switch_model"]["model_id"] == "gemini-embedding-001"
    assert actions["switch_model"]["dimension"] == 3072
    assert actions["reembed"]["dataset_id"] == str(dataset.dataset_id)
    mock_pgvector_store.search.assert_not_called()


@pytest.mark.asyncio
async def test_same_model_name_from_another_provider_is_a_mismatch(semantic_service):
    # Identical model id and width, different provider: never assumed compatible.
    dataset = _dataset("openrouter", "test-model-1", 768)
    db = AsyncMock()
    db.execute.side_effect = [MagicMock(scalar_one_or_none=lambda: dataset)]

    result = await semantic_service.semantic_search(
        db=db, user_id=uuid.uuid4(), user_query="Test query", dataset_id=dataset.dataset_id
    )

    assert result["error"] == ErrorCode.MODEL_MISMATCH


@pytest.mark.asyncio
async def test_nothing_indexed_for_active_model_explains_the_other_models(
    semantic_service, mock_pgvector_store, groups
):
    groups[:] = [_group("builtin", "BAAI/bge-small-en-v1.5", 384, ["Orders", "Users"])]
    empty = MagicMock()
    empty.rows = []
    mock_pgvector_store.search.return_value = empty

    result = await semantic_service.semantic_search(db=AsyncMock(), user_id=uuid.uuid4(), user_query="Test query")

    assert result["success"] is False
    assert result["error"] == ErrorCode.MODEL_MISMATCH
    assert "2 dataset(s)" in result["message"]
    switch, reembed = result["options"]
    assert switch["action"] == "switch_model" and switch["provider"] == "builtin"
    assert reembed["action"] == "reembed_all" and len(reembed["dataset_ids"]) == 2


@pytest.mark.asyncio
async def test_results_still_list_datasets_left_out_by_model(semantic_service, groups):
    groups.append(_group("google", "gemini-embedding-001", 3072, ["Payments"]))
    db = AsyncMock()
    db.execute.side_effect = [MagicMock(scalar_one_or_none=lambda: _template())]

    result = await semantic_service.semantic_search(db=db, user_id=uuid.uuid4(), user_query="Test query")

    assert result["success"] is True
    [excluded] = result["metadata"]["excluded_datasets"]
    assert excluded["model_id"] == "gemini-embedding-001"
    assert excluded["datasets"][0]["name"] == "Payments"
    assert {o["action"] for o in result["options"]} == {"switch_model", "reembed_all"}


@pytest.mark.asyncio
async def test_empty_stage1_results(semantic_service, mock_pgvector_store):
    db = AsyncMock()
    db.execute.side_effect = [MagicMock(scalar_one_or_none=lambda: _dataset())]
    empty = MagicMock()
    empty.rows = []
    mock_pgvector_store.search.return_value = empty

    result = await semantic_service.semantic_search(
        db=db, user_id=uuid.uuid4(), user_query="Test query", dataset_id=uuid.uuid4()
    )

    assert result["success"] is False
    assert result["error"] == "NO_RESULTS"


@pytest.mark.asyncio
async def test_missing_key_is_reported_in_plain_words(semantic_service):
    from app.llm.embeddings import EmbeddingError

    with patch(f"{MODULE}.embedder_for", AsyncMock(side_effect=EmbeddingError(
        "Using Google Gemini needs an API key. Add a Google Gemini connection in Settings → AI Providers.", "NO_KEY"
    ))):
        result = await semantic_service.semantic_search(db=AsyncMock(), user_id=uuid.uuid4(), user_query="q")

    assert result["error"] == "EMBEDDING_FAILED"
    assert "Settings → AI Providers" in result["message"]


@pytest.mark.asyncio
async def test_skip_compatibility_check(semantic_service):
    # Skipping the check means the only DB read is the template lookup.
    db = AsyncMock()
    db.execute.side_effect = [MagicMock(scalar_one_or_none=lambda: _template())]

    result = await semantic_service.semantic_search(
        db=db, user_id=uuid.uuid4(), user_query="Test query",
        dataset_id=uuid.uuid4(), skip_compatibility_check=True,
    )

    assert result["success"] is True
