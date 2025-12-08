"""
API v1 routes - Consolidated router for all v1 endpoints
No duplicate endpoints folder - all routes consolidated here

✅ Enterprise Template Builder with strict validation
✅ Approval workflow (draft → review → approved)
✅ Dataset generation only for approved templates
✅ Audit logging for security and compliance
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
    query,
    search,
    ranking,  # Two-Stage AI Ranking Engine
    user_data,
    user_settings,
    template_builder,
    audit_logs,
    runs
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

# === Search & Query ===
router.include_router(search.router, prefix="/search", tags=["Search"])
router.include_router(query.router, prefix="/query", tags=["Query Processing"])

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

# === Test Runs ===
# runs.py already has prefix="/runs"
router.include_router(runs.router, tags=["Test Runs"])


# === Root Level Stats Endpoint ===
@router.get("/stats")
async def get_global_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get global statistics for the dashboard (Vector DB Stats)
    
    Returns:
        Global statistics including total embeddings and intents
    """
    try:
        # Return structure matching Frontend StatsResponse
        return {
            "total_embeddings": 0,
            "intents": {},
            "model": "nomic-embed-text",
            "index_name": "embeddings_768"
        }
    except Exception as e:
        logger.error(f"Error getting global stats: {e}", exc_info=True)
        return {
            "total_embeddings": 0,
            "intents": {},
            "model": "unknown",
            "index_name": "unknown"
        }
