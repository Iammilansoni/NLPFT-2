"""
API v1 - Consolidated router for all v1 endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import (
    auth,
    email_verification,
    datasets,
    embeddings,
    embedding_validation,
    models,
    ranking,
    user_data,
    user_settings,
    template_builder,
    audit_logs,
    telemetry,
    model_validation,
    multi_model_query,
    llm_config,
    admin,
)
from app.core.postgres import get_db
from app.api.v1.auth import get_current_user
from app.models.database_models import User
from app.core.logger import logger

router = APIRouter(prefix="/v1")

# Authentication & User Management
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(email_verification.router, tags=["Email Verification"])
router.include_router(user_data.router, prefix="/user-data", tags=["User Data"])

# Template Builder
router.include_router(template_builder.router, tags=["Template Builder"])

# Datasets & Embeddings
router.include_router(datasets.router, tags=["Datasets"])
router.include_router(embeddings.router, prefix="/embeddings", tags=["Embeddings"])
router.include_router(embedding_validation.router, tags=["Embedding Validation"])

# AI Ranking Engine
router.include_router(ranking.router, prefix="/ranking", tags=["AI Ranking Engine"])

# Configuration
router.include_router(models.router, tags=["Models"])
router.include_router(user_settings.router, tags=["User Settings"])
router.include_router(llm_config.router, tags=["LLM Configuration"])

# Audit Logs
router.include_router(audit_logs.router, tags=["Audit Logs"])

# Multi-Model Embedding System
router.include_router(model_validation.router, tags=["Model Validation"])
router.include_router(multi_model_query.router, tags=["Multi-Model Query"])

# Performance Telemetry
router.include_router(telemetry.router, tags=["Performance Telemetry"])

# Admin
router.include_router(admin.router, tags=["Admin"])


# === Root Level Stats Endpoint ===
@router.get("/stats")
async def get_user_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user-specific dashboard statistics (Multi-Tenant Secure)
    
    Returns stats ONLY for the authenticated user:
    - total_embeddings: Count of user's vectors in Redis (across all models)
    - total_intents: Unique intent types from PostgreSQL csv_data
    - unique_apis: Unique API names from PostgreSQL csv_data
    - intents: Intent type distribution {intent: count}
    """
    try:
        from app.services.multi_model_redis_service import get_multi_model_redis_service
        from app.core.embedding_model_registry import get_embedding_registry
        from app.models.database_models import CSVData
        from sqlalchemy import select, func, distinct

        # Count vectors across all registered models
        embedding_count = 0
        try:
            redis_service = get_multi_model_redis_service()
            registry = get_embedding_registry()
            for model_id in registry.list_model_ids():
                try:
                    model_count = redis_service.count_vectors(model_id, current_user.u_id)
                    logger.debug(f"Model {model_id}: {model_count} vectors")
                    embedding_count += model_count
                except Exception as model_err:
                    logger.debug(f"Count failed for model {model_id}: {model_err}")
                    continue
        except Exception:
            embedding_count = 0

        # Intent distribution and unique API count from PostgreSQL
        intents = {}
        unique_api_count = 0
        try:
            # Coalesce intent_type -> data_category -> 'unknown'
            intent_expr = func.coalesce(CSVData.intent_type, CSVData.data_category, 'unknown').label('intent')
            intent_result = await db.execute(
                select(
                    intent_expr,
                    func.count().label('cnt')
                )
                .where(
                    CSVData.u_id == current_user.u_id
                )
                .group_by(intent_expr)
            )
            for row in intent_result:
                intent_name = row.intent or 'unknown'
                intents[intent_name] = row.cnt

            # Count unique API names
            api_result = await db.execute(
                select(func.count(distinct(CSVData.api_name)))
                .where(
                    CSVData.u_id == current_user.u_id,
                    CSVData.api_name.isnot(None),
                    CSVData.api_name != ''
                )
            )
            unique_api_count = api_result.scalar() or 0
        except Exception as e:
            logger.warning(f"Could not aggregate intents/APIs from DB: {e}")

        # Fetch user's active embedding model name for display
        active_model = "unknown"
        try:
            from app.models.database_models import UserSetting
            settings_result = await db.execute(
                select(UserSetting).where(UserSetting.u_id == current_user.u_id)
            )
            user_settings = settings_result.scalar_one_or_none()
            if user_settings and user_settings.default_embedding_model:
                active_model = user_settings.default_embedding_model
        except Exception:
            pass

        return {
            "total_embeddings": embedding_count,
            "total_intents": len(intents),
            "unique_apis": unique_api_count,
            "intents": intents,
            "model": active_model,
            "index_name": f"idx_vectors_{active_model.replace('-', '_')}"
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
