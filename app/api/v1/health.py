from datetime import datetime
from fastapi import APIRouter, Request

from app.models.schemas import HealthResponse
from app.core.database import db
from app.core.logger import logger

# cSpell:ignore faiss

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.
    Verifies all system components (dictionary, FAISS, embeddings, MongoDB, background worker).
    """
    checks = {}

    try:
        if hasattr(request.app.state, "dictionary_loader"):
            checks["dictionary"] = "healthy"
        else:
            checks["dictionary"] = "not_initialized"
        
        if hasattr(request.app.state, "faiss_manager"):
            checks["faiss_index"] = "healthy"
        else:
            checks["faiss_index"] = "not_initialized"

        if hasattr(request.app.state, "embedding_model"):
            checks["embedding_model"] = "healthy"
        else:
            checks["embedding_model"] = "not_initialized"

        try:
            await db.command("ping")   # runs {"ping":1} to verify DB is alive
            checks["mongodb"] = "healthy"
        except Exception as e:
            checks["mongodb"] = f"error: {str(e)}"
            logger.error(f"❌ MongoDB health check failed: {e}")

        if hasattr(request.app.state, "last_worker_heartbeat"):
            # Get last heartbeat timestamp
            last = request.app.state.last_worker_heartbeat
            delta = datetime.utcnow() - last

            if delta.total_seconds() < 300:
                checks["background_worker"] = "healthy"
            else:
                checks["background_worker"] = "stalled"
        else:
            checks["background_worker"] = "not_initialized"

        if all(status == "healthy" for status in checks.values()):
            overall_status = "healthy"
        elif any("error" in status or status == "stalled" for status in checks.values()):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

    except Exception as e:
        logger.error(f"❌ Health check crashed: {e}")
        checks["error"] = str(e)
        overall_status = "unhealthy"

    logger.info(f"Health Check → {overall_status} | {checks}")

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        checks=checks
    )