"""Optimized health check endpoints for NLPForge API (Docker-ready)."""

import psutil
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from typing import Dict, Any

from app.models.schemas import HealthResponse
from app.core.database import db_manager
from app.core.logger import logger
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


async def get_basic_status() -> Dict[str, str]:
    """Get basic system health status."""
    try:
        # Check database
        db_healthy = await db_manager.ping()
        
        # Check system resources
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        status = {
            "database": "healthy" if db_healthy else "unhealthy",
            "memory": "healthy" if memory.percent < 85 else "warning",
            "cpu": "healthy" if cpu_percent < 85 else "warning"
        }
        
        return status
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {"system": "error"}


@router.get("/", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Comprehensive health check endpoint.
    Optimized for Docker deployments.
    """
    start_time = datetime.now(timezone.utc)
    
    try:
        # Get basic status
        checks = await get_basic_status()
        
        # Add uptime if available
        if hasattr(request.app.state, 'startup_time'):
            uptime = (datetime.now(timezone.utc) - request.app.state.startup_time).total_seconds()
            checks["uptime"] = f"{uptime:.0f}s"
        
        # Calculate overall status
        overall_status = "healthy" if all(
            status in ["healthy", "ready"] for status in checks.values() 
            if not status.endswith("s")  # Skip uptime
        ) else "degraded"
        
        # Add check duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        checks["check_duration"] = f"{duration:.3f}s"
        
        return HealthResponse(
            status=overall_status,
            version=settings.app_version,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"❌ Health check crashed: {e}")
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            checks={"error": str(e)}
        )


@router.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check for Docker health checks.
    Simple and fast - perfect for Docker HEALTHCHECK.
    """
    try:
        # Essential check: database connectivity
        if await db_manager.ping():
            return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
        else:
            return {"status": "not_ready", "reason": "database_down", "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    except Exception as e:
        logger.error(f"❌ Readiness check failed: {e}")
        return {"status": "not_ready", "reason": "error", "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check for Docker containers.
    Always returns alive unless the process is completely broken.
    """
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}


@router.get("/simple")
async def simple_health_check() -> Dict[str, str]:
    """
    Ultra-simple health check for load balancers.
    """
    try:
        db_ok = await db_manager.ping()
        status = "healthy" if db_ok else "unhealthy"
        return {"status": status, "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    except Exception:
        return {"status": "unhealthy", "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}


@router.get("/metrics")
async def health_metrics() -> Dict[str, Any]:
    """
    Essential metrics for monitoring (Docker-optimized).
    """
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "metrics": {
                "memory_percent": memory.percent,
                "cpu_percent": cpu_percent,
                "memory_available_mb": round(memory.available / 1024 / 1024),
                "process_id": psutil.Process().pid
            }
        }
    except Exception as e:
        logger.error(f"❌ Metrics failed: {e}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "error": str(e)
        }
