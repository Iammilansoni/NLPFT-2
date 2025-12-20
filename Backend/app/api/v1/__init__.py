"""
API v1 routes - Consolidated router for all v1 endpoints
No duplicate endpoints folder - all routes consolidated here

Features:
- Enterprise Template Builder with strict validation
- Approval workflow (draft > review > approved)
- Dataset generation only for approved templates
- Audit logging for security and compliance
- Multi-Model Embedding System (dimension-safe, tenant-safe)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Import v1 routers (no more endpoints folder duplicates)
from app.api.v1 import (
    auth,
    email_verification,
    datasets,
    embeddings,
    embedding_validation,
    models,
    ranking,  # Two-Stage AI Ranking Engine
    user_data,
    user_settings,
    template_builder,
    audit_logs,
    telemetry,  # Performance Telemetry
    # Multi-Model Embedding System
    model_validation,  # Model compatibility checks
    multi_model_query,  # Semantic search with model governance
)
from app.core.postgres import get_db
from app.api.v1.auth import get_current_user
from app.models.database_models import User
from app.core.logger import logger

# Create main v1 router
router = APIRouter(prefix="/v1")

# === Authentication & User Management ===
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# email_verification.router already has prefix="/auth"
router.include_router(email_verification.router, tags=["Email Verification"])
router.include_router(user_data.router, prefix="/user-data", tags=["User Data"])

# === Enterprise Template Builder (NEW) ===
router.include_router(template_builder.router, tags=["Template Builder"])

# === Dataset & Embeddings ===
# datasets.py already has prefix="/datasets"
router.include_router(datasets.router, tags=["Datasets"])
router.include_router(embeddings.router, prefix="/embeddings", tags=["Embeddings"])
# embedding_validation.py already has prefix="/embeddings"
router.include_router(embedding_validation.router, tags=["Embedding Validation"])

# === AI Ranking Engine (Two-Stage: Vector + FlashRank) ===
router.include_router(ranking.router, prefix="/ranking", tags=["AI Ranking Engine"])

# === Configuration ===
# models.py already has prefix="/models"
router.include_router(models.router, tags=["Models"])
# user_settings.py already has prefix="/user"
router.include_router(user_settings.router, tags=["User Settings"])

# === Audit Logs ===
# audit_logs.py already has prefix="/audit"
router.include_router(audit_logs.router, tags=["Audit Logs"])

# === Multi-Model Embedding System (NEW) ===
# Model validation and compatibility checking
router.include_router(model_validation.router, tags=["Model Validation"])
# Multi-model query with semantic search
router.include_router(multi_model_query.router, tags=["Multi-Model Query"])

# === Performance Telemetry ===
# telemetry.py already has prefix="/telemetry"
router.include_router(telemetry.router, tags=["Performance Telemetry"])


# === Root Level Stats Endpoint ===
@router.get("/stats")
async def get_user_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user-specific dashboard statistics (Multi-Tenant Secure)
    
    Returns stats ONLY for the authenticated user:
    - total_embeddings: Count of user's vectors in Redis
    - total_intents: Unique intent types in user's data
    - unique_apis: Unique API names in user's data
    """
    try:
        # Get actual embedding count from Redis
        from app.services.redis_vector_service import get_redis_vector_service
        import redis
        from app.core.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
        
        redis_service = get_redis_vector_service()
        
        # Count embeddings for this user
        embedding_count = redis_service.count_embeddings(current_user.u_id)
        
        # Get unique intents and APIs by scanning user's embeddings
        intents = {}
        unique_apis = set()
        
        try:
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=False)
            user_id = str(current_user.u_id)
            pattern = f"embedding:{user_id}:*"
            
            for key in r.scan_iter(match=pattern.encode(), count=100):
                try:
                    data = r.json().get(key)
                    if data:
                        # Count intents
                        intent = data.get('intent_type') or data.get('scenario_type') or 'unknown'
                        if isinstance(intent, bytes):
                            intent = intent.decode()
                        intents[intent] = intents.get(intent, 0) + 1
                        
                        # Count unique APIs
                        api = data.get('api', '')
                        if isinstance(api, bytes):
                            api = api.decode()
                        if api:
                            unique_apis.add(api)
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Could not aggregate intents/APIs: {e}")
        
        # Return structure matching Frontend StatsResponse
        return {
            "total_embeddings": embedding_count,
            "total_intents": len(intents),
            "unique_apis": len(unique_apis),
            "intents": intents,
            "model": "nomic-embed-text",
            "index_name": "embeddings_768"
        }
    except Exception as e:
        logger.error(f"Error getting global stats: {e}", exc_info=True)
        return {
            "total_embeddings": 0,
            "total_intents": 0,
            "unique_apis": 0,
            "intents": {},
            "model": "unknown",
            "index_name": "unknown"
        }
