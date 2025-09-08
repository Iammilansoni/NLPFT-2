"""Health check endpoints for NLPForge API."""

import asyncio
import psutil
from datetime import datetime
from fastapi import APIRouter, Request
from typing import Dict, Any

from app.models.schemas import HealthResponse
from app.core.database import db_manager
from app.core.logger import logger, log_health_check
from app.core.config import settings

# cSpell:ignore faiss

router = APIRouter(prefix="/health", tags=["health"])


async def check_database() -> Dict[str, str]:
    """Check database connectivity."""
    try:
        if await db_manager.ping():
            return {"mongodb": "healthy"}
        else:
            return {"mongodb": "disconnected"}
    except Exception as e:
        logger.error(f"❌ MongoDB health check failed: {e}")
        return {"mongodb": f"error: {str(e)}"}


async def check_system_resources() -> Dict[str, str]:
    """Check system resource health."""
    checks = {}
    
    try:
        # Memory check
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            checks["memory"] = f"critical: {memory.percent:.1f}% used"
        elif memory.percent > 75:
            checks["memory"] = f"warning: {memory.percent:.1f}% used"
        else:
            checks["memory"] = "healthy"
        
        # CPU check
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            checks["cpu"] = f"critical: {cpu_percent:.1f}% used"
        elif cpu_percent > 75:
            checks["cpu"] = f"warning: {cpu_percent:.1f}% used"
        else:
            checks["cpu"] = "healthy"
            
        # Disk check
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > 90:
            checks["disk"] = f"critical: {disk_percent:.1f}% used"
        elif disk_percent > 75:
            checks["disk"] = f"warning: {disk_percent:.1f}% used"
        else:
            checks["disk"] = "healthy"
            
    except Exception as e:
        logger.error(f"❌ System resource check failed: {e}")
        checks["system_resources"] = f"error: {str(e)}"
    
    return checks


async def check_nlp_components(app_state) -> Dict[str, str]:
    """Check NLP component health."""
    checks = {}
    
    # Dictionary loader
    if hasattr(app_state, "dictionary_loader") and app_state.dictionary_loader:
        checks["dictionary"] = "healthy"
    else:
        checks["dictionary"] = "not_initialized"
    
    # FAISS index
    if hasattr(app_state, "faiss_manager") and app_state.faiss_manager:
        checks["faiss_index"] = "healthy"
    else:
        checks["faiss_index"] = "not_initialized"
    
    # Embedding model
    if hasattr(app_state, "embedding_model") and app_state.embedding_model:
        checks["embedding_model"] = "healthy"
    else:
        checks["embedding_model"] = "not_initialized"
    
    return checks


async def check_background_worker(app_state) -> Dict[str, str]:
    """Check background worker health."""
    if hasattr(app_state, "last_worker_heartbeat"):
        last = app_state.last_worker_heartbeat
        delta = datetime.utcnow() - last
        
        if delta.total_seconds() < 300:  # 5 minutes
            return {"background_worker": "healthy"}
        elif delta.total_seconds() < 900:  # 15 minutes
            return {"background_worker": "stalled"}
        else:
            return {"background_worker": "dead"}
    else:
        return {"background_worker": "not_initialized"}


def calculate_overall_status(checks: Dict[str, str]) -> str:
    """Calculate overall system status based on individual checks."""
    statuses = list(checks.values())
    
    # Count different status types
    error_count = sum(1 for status in statuses if "error" in status.lower())
    critical_count = sum(1 for status in statuses if "critical" in status.lower())
    warning_count = sum(1 for status in statuses if "warning" in status.lower())
    stalled_count = sum(1 for status in statuses if "stalled" in status.lower())
    dead_count = sum(1 for status in statuses if "dead" in status.lower())
    
    # Determine overall status
    if error_count > 0 or critical_count > 0 or dead_count > 0:
        return "unhealthy"
    elif stalled_count > 0 or warning_count > 0:
        return "degraded"
    elif all(status == "healthy" for status in statuses):
        return "healthy"
    else:
        return "degraded"


@router.get("/", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Comprehensive health check endpoint.
    
    Verifies all system components:
    - Database connectivity (MongoDB)
    - NLP components (dictionary, FAISS, embeddings)
    - Background worker status
    - System resources (CPU, memory, disk)
    """
    start_time = datetime.utcnow()
    all_checks = {}

    try:
        # Run all health checks concurrently for better performance
        db_check_task = check_database()
        resource_check_task = check_system_resources()
        nlp_check_task = check_nlp_components(request.app.state)
        worker_check_task = check_background_worker(request.app.state)
        
        # Wait for all checks to complete
        db_checks, resource_checks, nlp_checks, worker_checks = await asyncio.gather(
            db_check_task,
            resource_check_task,
            nlp_check_task,
            worker_check_task,
            return_exceptions=True
        )
        
        # Combine all checks
        if isinstance(db_checks, dict):
            all_checks.update(db_checks)
        else:
            all_checks["database"] = f"error: {str(db_checks)}"
            
        if isinstance(resource_checks, dict):
            all_checks.update(resource_checks)
        else:
            all_checks["resources"] = f"error: {str(resource_checks)}"
            
        if isinstance(nlp_checks, dict):
            all_checks.update(nlp_checks)
        else:
            all_checks["nlp"] = f"error: {str(nlp_checks)}"
            
        if isinstance(worker_checks, dict):
            all_checks.update(worker_checks)
        else:
            all_checks["worker"] = f"error: {str(worker_checks)}"

        # Calculate overall status
        overall_status = calculate_overall_status(all_checks)
        
        # Add performance metrics
        check_duration = (datetime.utcnow() - start_time).total_seconds()
        all_checks["health_check_duration"] = f"{check_duration:.3f}s"
        
        # Add uptime if available
        if hasattr(request.app.state, 'startup_time'):
            uptime = (datetime.utcnow() - request.app.state.startup_time).total_seconds()
            all_checks["uptime"] = f"{uptime:.0f}s"

    except Exception as e:
        logger.error(f"❌ Health check crashed: {e}")
        all_checks = {"error": str(e)}
        overall_status = "unhealthy"

    # Log the health check results
    log_health_check(overall_status, all_checks)

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat() + "Z",
        checks=all_checks
    )


@router.get("/simple")
async def simple_health_check() -> Dict[str, str]:
    """
    Simple health check endpoint for load balancers.
    Returns basic status without detailed checks.
    """
    try:
        # Quick database ping
        if await db_manager.ping():
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}
        else:
            return {"status": "unhealthy", "timestamp": datetime.utcnow().isoformat() + "Z"}
    except Exception:
        return {"status": "unhealthy", "timestamp": datetime.utcnow().isoformat() + "Z"}


@router.get("/ready")
async def readiness_check(request: Request) -> Dict[str, str]:
    """
    Readiness check endpoint for Kubernetes.
    Checks if the service is ready to accept traffic.
    """
    try:
        # Check essential components
        ready = True
        
        # Database must be connected
        if not await db_manager.ping():
            ready = False
        
        # Essential NLP components should be initialized
        # (can be relaxed based on requirements)
        if not (hasattr(request.app.state, "dictionary_loader") and 
                hasattr(request.app.state, "faiss_manager")):
            # For now, we'll allow the service to be ready even without NLP components
            pass
        
        status = "ready" if ready else "not_ready"
        return {"status": status, "timestamp": datetime.utcnow().isoformat() + "Z"}
        
    except Exception as e:
        logger.error(f"❌ Readiness check failed: {e}")
        return {"status": "not_ready", "timestamp": datetime.utcnow().isoformat() + "Z"}


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint for Kubernetes.
    Checks if the service is alive and should not be restarted.
    """
    # For liveness, we just need to respond
    # This endpoint should always return healthy unless the process is completely broken
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat() + "Z"}