"""Unit tests for the routing pipeline orchestration (all I/O mocked)."""

import uuid
from contextlib import ExitStack, asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas.embedding_schemas import ErrorCode
from app.services.multi_model_semantic_service import MultiModelSemanticRetrievalService
from app.services.structured_extraction_service import ExtractionResult

T1 = "00000000-0000-0000-0000-000000000001"
T2 = "00000000-0000-0000-0000-000000000002"
MODULE = "app.services.multi_model_semantic_service"


@pytest.fixture
def mock_embedder():
    # One runtime embedder per deployment (EXECUTION_MODE), not per user.
    embedder = AsyncMock()
    embedder.model_id = "test-model-1"
    embedder.dimension = 768
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
def semantic_service(mock_embedder, mock_pgvector_store, mock_extractor):
    @asynccontextmanager
    async def _fake_tenant_session(user_id):
        yield AsyncMock()

    # tenant_session is entered inside semantic_search() on every call, so the
    # patch must stay active for the whole test, not just construction. Letting
    # the real one run would try set_config() against CI's SQLite.
    with ExitStack() as stack:
        stack.enter_context(patch(f"{MODULE}.get_embedder", return_value=mock_embedder))
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


@pytest.mark.asyncio
async def test_semantic_search_success_flow(
    semantic_service, mock_pgvector_store, mock_extractor
):
    db = AsyncMock()
    db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: MagicMock(embedding_model="test-model-1")),
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
    mock_pgvector_store.search.assert_called_once()
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
async def test_model_mismatch_rejection(semantic_service):
    dataset_id = uuid.uuid4()
    db = AsyncMock()
    db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: MagicMock(
            dataset_id=dataset_id, embedding_model="some-other-model"))
    ]

    result = await semantic_service.semantic_search(
        db=db, user_id=uuid.uuid4(), user_query="Test query", dataset_id=dataset_id
    )

    assert result["success"] is False
    assert result["error"] == ErrorCode.MODEL_MISMATCH


@pytest.mark.asyncio
async def test_empty_stage1_results(semantic_service, mock_pgvector_store):
    dataset_id = uuid.uuid4()
    db = AsyncMock()
    db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: MagicMock(
            dataset_id=dataset_id, embedding_model="test-model-1"))
    ]
    empty = MagicMock()
    empty.rows = []
    mock_pgvector_store.search.return_value = empty

    result = await semantic_service.semantic_search(
        db=db, user_id=uuid.uuid4(), user_query="Test query", dataset_id=dataset_id
    )

    assert result["success"] is False
    assert result["error"] == "NO_RESULTS"


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
