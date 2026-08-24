import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from typing import Dict, Any, List

from app.services.multi_model_semantic_service import MultiModelSemanticRetrievalService
from app.models.schemas.embedding_schemas import ErrorCode

@pytest.fixture
def mock_registry():
    return MagicMock()

@pytest.fixture
def mock_settings_service():
    service = AsyncMock()
    # By default, mock active model setup
    service.get_active_embedding_model_async.return_value = ("test-model-1", 768, MagicMock())
    # By default, return compatible
    service.validate_model_for_search.return_value = {"compatible": True}
    return service

@pytest.fixture
def mock_redis_service():
    service = MagicMock()
    # return matching stages
    service.search_similar_vectors.return_value = [
        {"row_id": "r1", "t_id": "00000000-0000-0000-0000-000000000001", "similarity": 0.95, "confidence_score": 0.9, "query": "test query", "intent_type": "valid"},
        {"row_id": "r2", "t_id": "00000000-0000-0000-0000-000000000002", "similarity": 0.85, "confidence_score": 0.8, "query": "another query", "intent_type": "edge"}
    ]
    return service

@pytest.fixture
def mock_ollama_service():
    service = AsyncMock()
    # Mock embedding generation
    service.generate_embedding.return_value = [0.1] * 768
    return service

@pytest.fixture
def mock_slot_extractor():
    service = AsyncMock()
    # Mock slot extraction
    service.extract_slots.return_value = {"account_id": "12345"}
    service.extract_url_from_query = MagicMock(return_value=(None, None))
    return service

@pytest.fixture
def semantic_service(mock_registry, mock_settings_service, mock_redis_service, mock_ollama_service, mock_slot_extractor):
    with patch("app.services.multi_model_semantic_service.get_embedding_registry", return_value=mock_registry), \
         patch("app.services.multi_model_semantic_service.get_user_embedding_settings_service", return_value=mock_settings_service), \
         patch("app.services.multi_model_semantic_service.get_multi_model_redis_service", return_value=mock_redis_service), \
         patch("app.services.multi_model_semantic_service.get_ollama_service", return_value=mock_ollama_service), \
         patch("app.services.multi_model_semantic_service.get_slot_extraction_service", return_value=mock_slot_extractor):
        
        service = MultiModelSemanticRetrievalService()
        return service

@pytest.fixture
def mock_db():
    db = AsyncMock()
    
    # db.execute is used for dataset check, and then for template fetch
    return db

@pytest.mark.asyncio
async def test_semantic_search_success_flow(semantic_service, mock_db, mock_redis_service, mock_slot_extractor):
    user_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    
    # Needs a mock template response for the DB hydration stage
    mock_template = MagicMock()
    mock_template.t_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    mock_template.api_name = "Test API"
    mock_template.endpoint = "/api/test"
    mock_template.method = "POST"
    
    # db.execute is called twice: once for dataset, once for template
    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: MagicMock(t_id=uuid.uuid4(), embedding_model="test-model-1")), 
        MagicMock(scalar_one_or_none=lambda: mock_template)
    ]

    result = await semantic_service.semantic_search(
        db=mock_db,
        user_id=user_id,
        user_query="Find user by account id 12345",
        top_k=5,
        dataset_id=dataset_id,
        include_slot_extraction=True
    )
    
    assert result["success"] is True
    assert "stage1_vector_search" in result
    assert "stage2_reranking" in result
    assert "final_output" in result
    assert "extracted_request_body" in result
    assert result["extracted_request_body"] == {"account_id": "12345"}
    
    # Verify methods were called
    mock_redis_service.search_similar_vectors.assert_called_once()
    mock_slot_extractor.extract_slots.assert_called_once()

@pytest.mark.asyncio
async def test_model_mismatch_rejection(semantic_service, mock_db):
    user_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    
    # Force a mismatch by dataset returning a different embedding model
    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: MagicMock(dataset_id=dataset_id, embedding_model="some-other-model"))
    ]
    
    result = await semantic_service.semantic_search(
        db=mock_db,
        user_id=user_id,
        user_query="Test query",
        dataset_id=dataset_id
    )
    
    assert result["success"] is False
    assert result["error"] == ErrorCode.MODEL_MISMATCH

@pytest.mark.asyncio
async def test_empty_stage1_results(semantic_service, mock_db, mock_redis_service):
    user_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    
    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: MagicMock(dataset_id=dataset_id, embedding_model="test-model-1"))
    ]
    
    # Return empty from redis
    mock_redis_service.search_similar_vectors.return_value = []
    
    result = await semantic_service.semantic_search(
        db=mock_db,
        user_id=user_id,
        user_query="Test query",
        dataset_id=dataset_id
    )
    
    assert result["success"] is False
    assert result["error"] == "NO_RESULTS"

@pytest.mark.asyncio
async def test_skip_compatibility_check(semantic_service, mock_db, mock_redis_service):
    user_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    
    # DB mock for dataset returns mismatch, but we skip check so it won't matter
    # The actual semantic_search won't query dataset if skip_compatibility_check=True
    # BUT wait, the code says `if not skip_compatibility_check and (dataset_id or template_id):`
    # So if we skip, it will NOT query the dataset table!
    # Therefore, the only db query will be the template query.
    
    mock_template = MagicMock()
    mock_template.t_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    mock_template.api_name = "Test API"
    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: mock_template)
    ]

    result = await semantic_service.semantic_search(
        db=mock_db,
        user_id=user_id,
        user_query="Test query",
        dataset_id=dataset_id,
        skip_compatibility_check=True
    )
    
    assert result["success"] is True
