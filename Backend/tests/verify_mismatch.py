
import sys
import os
import asyncio
import uuid
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

# Add Backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.embedding_service import EnhancedEmbeddingService
from app.models.database_models import UserSettings, Metadata
from fastapi import HTTPException

async def verify_mismatch_logic():
    print("🚀 Starting Model Mismatch Verification...")
    
    service = EnhancedEmbeddingService()
    
    # Mock DB Session
    mock_db = MagicMock()
    
    # Test Data
    user_id = uuid.uuid4()
    template_id = uuid.uuid4()
    
    # Scenario 1: Mismatch (Embedded with A, User wants B)
    print("\n🧪 Scenario 1: Mismatch (Embedded with 'all-minilm', User wants 'nomic-embed-text')")
    
    # Mock User Settings (User wants 'nomic-embed-text')
    mock_settings = UserSettings(
        u_id=user_id,
        default_embedding_model="nomic-embed-text",
        embedding_dimension=768
    )
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_settings, # For user settings query
        Metadata(      # For metadata query
            template_id=template_id,
            remarks={"embedding_info": {"embedded_with_model": "all-minilm"}}
        )
    ]
    
    try:
        await service.search_similar_test_cases(
            user_id=user_id,
            template_id=template_id,
            query="test",
            db=mock_db
        )
        print("❌ Failed: Should have raised HTTPException")
    except HTTPException as e:
        if e.status_code == 409:
            print("✅ Success: Caught expected 409 Conflict")
            print(f"   Message: {e.detail['message']}")
        else:
            print(f"❌ Failed: Unexpected status code {e.status_code}")
    except Exception as e:
        print(f"❌ Failed: Unexpected exception {e}")

    # Scenario 2: Match (Embedded with A, User wants A)
    print("\n🧪 Scenario 2: Match (Embedded with 'all-minilm', User wants 'all-minilm')")
    
    # Mock User Settings (User wants 'all-minilm')
    mock_settings_match = UserSettings(
        u_id=user_id,
        default_embedding_model="all-minilm",
        embedding_dimension=384
    )
    
    # Reset mocks
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_settings_match, # For user settings query
        Metadata(            # For metadata query
            template_id=template_id,
            remarks={"embedding_info": {"embedded_with_model": "all-minilm"}}
        )
    ]
    
    # Mock Ollama service to avoid actual calls
    service.ollama_service.generate_embedding = AsyncMock(return_value=[0.1]*384)
    service.redis_service.redis_client.ft = MagicMock()
    service.redis_service.redis_client.ft.return_value.search.return_value.docs = []

    try:
        await service.search_similar_test_cases(
            user_id=user_id,
            template_id=template_id,
            query="test",
            db=mock_db
        )
        print("✅ Success: Search proceeded without error")
    except Exception as e:
        print(f"❌ Failed: Unexpected exception {e}")

    print("\n✨ Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_mismatch_logic())
