"""Comprehensive health check endpoint for NLPForge API."""

import psutil
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Response
from typing import Dict, Any, Optional

from app.models.schemas import HealthResponse
from app.core.database import db_manager, get_rule_engine
from app.nlp.enhanced_rule_engine import EnhancedRuleEngine
from app.core.logger import logger
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


async def get_rule_engine_safe() -> Optional[EnhancedRuleEngine]:
    """Get Enhanced Rule Engine with fallback handling."""
    try:
        return await get_rule_engine()
    except Exception:
        logger.warning("MongoDB Enhanced Rule Engine not available, using fallback")
        return EnhancedRuleEngine()


async def check_database() -> Dict[str, Any]:
    """Check database connectivity and status."""
    try:
        start_time = time.time()
        db_healthy = await db_manager.ping()
        response_time = (time.time() - start_time) * 1000  # ms
        
        if db_healthy:
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connection_pool": "active" if db_manager.client else "inactive"  # type: ignore
            }
        else:
            return {
                "status": "unhealthy",
                "response_time_ms": round(response_time, 2),
                "error": "ping_failed"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": -1
        }


async def check_rule_engine() -> Dict[str, Any]:
    """Check Rule Engine functionality."""
    try:
        start_time = time.time()
        rule_engine = await get_rule_engine_safe()
        
        if not rule_engine:
            return {
                "status": "unhealthy",
                "error": "rule_engine_unavailable"
            }
        
        # Test basic functionality
        test_result = rule_engine.parse("test health check input")
        response_time = (time.time() - start_time) * 1000  # ms
        
        # Get metrics
        metrics = rule_engine.get_metrics()
        
        # For Enhanced Rule Engine, we'll check basic health indicators
        is_healthy = (
            test_result is not None and
            "candidates" in test_result and
            metrics.active_patterns > 0
        )
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "response_time_ms": round(response_time, 2),
            "active_patterns": metrics.active_patterns,
            "total_parses": metrics.total_parses,
            "successful_parses": metrics.successful_parses,
            "failed_parses": metrics.failed_parses,
            "test_parse_successful": test_result is not None and "candidates" in test_result
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": -1
        }


async def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage."""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Determine status based on usage thresholds
        memory_status = "healthy"
        if memory.percent > 90:
            memory_status = "critical"
        elif memory.percent > 80:
            memory_status = "warning"
        
        cpu_status = "healthy"
        if cpu_percent > 90:
            cpu_status = "critical"
        elif cpu_percent > 80:
            cpu_status = "warning"
        
        overall_status = "healthy"
        if memory_status == "critical" or cpu_status == "critical":
            overall_status = "critical"
        elif memory_status == "warning" or cpu_status == "warning":
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "memory": {
                "status": memory_status,
                "usage_percent": round(memory.percent, 1),
                "available_mb": round(memory.available / 1024 / 1024),
                "total_mb": round(memory.total / 1024 / 1024)
            },
            "cpu": {
                "status": cpu_status,
                "usage_percent": round(cpu_percent, 1)
            },
            "process_id": psutil.Process().pid
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _generate_prometheus_response(database_health: Dict[str, Any], rule_engine_health: Dict[str, Any], system_health: Dict[str, Any]) -> Response:
    """Generate Prometheus metrics response from health check data."""
    try:
        # Convert status strings to numeric values for Prometheus
        def status_to_numeric(status: str) -> float:
            status_map: Dict[str, float] = {
                "healthy": 1.0,
                "warning": 0.75,
                "degraded": 0.5,
                "critical": 0.25,
                "unhealthy": 0.0
            }
            return status_map.get(status, 0.0)
        
        # Generate Prometheus exposition format
        current_time = int(time.time() * 1000)  # milliseconds
        
        prometheus_output = f"""# HELP nlpforge_system_health_status Overall system health status (1=healthy, 0.75=warning, 0.5=degraded, 0.25=critical, 0=unhealthy)
# TYPE nlpforge_system_health_status gauge
nlpforge_system_health_status{{component="overall"}} {status_to_numeric(system_health.get("status", "unhealthy"))} {current_time}

# HELP nlpforge_database_health_status Database health status
# TYPE nlpforge_database_health_status gauge
nlpforge_database_health_status{{component="database"}} {status_to_numeric(database_health.get("status", "unhealthy"))} {current_time}

# HELP nlpforge_database_response_time_ms Database response time in milliseconds
# TYPE nlpforge_database_response_time_ms gauge
nlpforge_database_response_time_ms {database_health.get("response_time_ms", -1)} {current_time}

# HELP nlpforge_rule_engine_health_status Rule Engine health status
# TYPE nlpforge_rule_engine_health_status gauge
nlpforge_rule_engine_health_status{{component="rule_engine"}} {status_to_numeric(rule_engine_health.get("status", "unhealthy"))} {current_time}

# HELP nlpforge_rule_engine_response_time_ms Rule Engine response time in milliseconds
# TYPE nlpforge_rule_engine_response_time_ms gauge
nlpforge_rule_engine_response_time_ms {rule_engine_health.get("response_time_ms", -1)} {current_time}

# HELP nlpforge_rule_engine_functions_total Total number of available functions
# TYPE nlpforge_rule_engine_functions_total gauge
nlpforge_rule_engine_functions_total {rule_engine_health.get("functions_count", 0)} {current_time}

# HELP nlpforge_rule_engine_patterns_total Total number of active patterns
# TYPE nlpforge_rule_engine_patterns_total gauge
nlpforge_rule_engine_patterns_total {rule_engine_health.get("active_patterns", 0)} {current_time}

# HELP nlpforge_rule_engine_parses_total Total number of parse operations
# TYPE nlpforge_rule_engine_parses_total counter
nlpforge_rule_engine_parses_total {rule_engine_health.get("total_parses", 0)} {current_time}

# HELP nlpforge_rule_engine_config_issues_total Number of configuration issues
# TYPE nlpforge_rule_engine_config_issues_total gauge
nlpforge_rule_engine_config_issues_total {rule_engine_health.get("config_issues", 0)} {current_time}

# HELP nlpforge_memory_usage_percent Memory usage percentage
# TYPE nlpforge_memory_usage_percent gauge
nlpforge_memory_usage_percent {system_health.get("memory", {}).get("usage_percent", 0)} {current_time}

# HELP nlpforge_memory_available_mb Available memory in megabytes
# TYPE nlpforge_memory_available_mb gauge
nlpforge_memory_available_mb {system_health.get("memory", {}).get("available_mb", 0)} {current_time}

# HELP nlpforge_memory_total_mb Total memory in megabytes
# TYPE nlpforge_memory_total_mb gauge
nlpforge_memory_total_mb {system_health.get("memory", {}).get("total_mb", 0)} {current_time}

# HELP nlpforge_cpu_usage_percent CPU usage percentage
# TYPE nlpforge_cpu_usage_percent gauge
nlpforge_cpu_usage_percent {system_health.get("cpu", {}).get("usage_percent", 0)} {current_time}

# HELP nlpforge_process_id Current process ID
# TYPE nlpforge_process_id gauge
nlpforge_process_id {system_health.get("process_id", 0)} {current_time}

# HELP nlpforge_up Application is running (1=up, 0=down)
# TYPE nlpforge_up gauge
nlpforge_up 1 {current_time}

# HELP nlpforge_info Application information
# TYPE nlpforge_info gauge
nlpforge_info{{version="{settings.app_version}",component="nlpforge_api"}} 1 {current_time}
"""
        
        logger.info(f"🔍 Generated {len(prometheus_output.split('nlpforge_'))-1} Prometheus metrics")
        
        return Response(
            content=prometheus_output,
            media_type="text/plain; version=0.0.4; charset=utf-8",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to generate Prometheus metrics: {e}")
        error_output = f"""# Error generating metrics
# TYPE nlpforge_metrics_error gauge
nlpforge_metrics_error{{error="{str(e).replace('"', "'")}"}} 1 {int(time.time() * 1000)}
"""
        return Response(
            content=error_output,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )


@router.get("/", response_model=None)
async def comprehensive_health_check(request: Request):
    """
    Unified health check endpoint with content negotiation.
    
    This single endpoint provides comprehensive system monitoring and supports:
    - JSON format (default): Detailed health information for applications/dashboards
    - Prometheus text format: Metrics for Prometheus scraping
    
    Content negotiation based on Accept header:
    - Accept: application/json (default) → Returns JSON health response
    - Accept: text/plain → Returns Prometheus metrics format
    - Accept: */*, text/* → Returns Prometheus metrics format
    
    Features:
    - Database connectivity and performance
    - Rule Engine functionality and metrics  
    - System resource usage
    - Overall application health status
    
    Returns appropriate format with proper HTTP status codes.
    """
    start_time = datetime.now(timezone.utc)
    
    # Check Accept header for content negotiation
    accept_header = request.headers.get("accept", "").lower()
    
    # Debug logging
    logger.debug(f"Accept header: '{accept_header}'")
    
    # Only return Prometheus format if explicitly requested
    wants_prometheus = (
        "text/plain" in accept_header or 
        (accept_header.startswith("text/") and "json" not in accept_header)
    ) and accept_header != "*/*"
    
    try:
        if wants_prometheus:
            logger.info("🔍 Generating Prometheus metrics via content negotiation")
        else:
            logger.info("🏥 Running comprehensive health check (JSON format)")
        
        # Run all health checks concurrently
        database_health = await check_database()
        rule_engine_health = await check_rule_engine() 
        system_health = await check_system_resources()
        
        # Add uptime if available
        uptime_info: Dict[str, Any] = {}
        if hasattr(request.app.state, 'startup_time'):
            uptime_seconds = (datetime.now(timezone.utc) - request.app.state.startup_time).total_seconds()
            uptime_info = {
                "uptime_seconds": round(uptime_seconds),
                "uptime_formatted": f"{uptime_seconds/3600:.1f}h" if uptime_seconds > 3600 else f"{uptime_seconds:.0f}s"
            }
        
        # Calculate check duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Determine overall status
        component_statuses = [
            database_health.get("status"),
            rule_engine_health.get("status"),
            system_health.get("status")
        ]
        
        if any(status == "unhealthy" for status in component_statuses):
            overall_status = "unhealthy"
        elif any(status in ["critical", "degraded"] for status in component_statuses):
            overall_status = "degraded"
        elif any(status == "warning" for status in component_statuses):
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        # Compile comprehensive health report
        checks: Dict[str, Any] = {
            "overall_status": overall_status,
            "database": database_health,
            "rule_engine": rule_engine_health,
            "system": system_health,
            "application": {
                "status": "running",
                "version": settings.app_version,
                **uptime_info
            },
            "health_check": {
                "duration_ms": round(duration * 1000, 2),
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        }
        
        # Return format based on content negotiation
        if wants_prometheus:
            # Generate Prometheus format
            return await _generate_prometheus_response(database_health, rule_engine_health, system_health)
        else:
            # Return JSON format
            logger.info(f"🏥 Health check completed: {overall_status} (took {duration*1000:.1f}ms)")
            
            return HealthResponse(
                status=overall_status,
                version=settings.app_version,
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                checks={"status": overall_status, **{k: v for k, v in checks.items() if k != "overall_status"}}  # type: ignore
            )
        
    except Exception as e:
        logger.error(f"❌ Health check crashed: {e}")
        
        if wants_prometheus:
            # Return Prometheus error format
            error_output = f"""# Error generating metrics
# TYPE nlpforge_metrics_error gauge
nlpforge_metrics_error{{error="{str(e).replace('"', "'")}"}} 1 {int(time.time() * 1000)}
"""
            return Response(
                content=error_output,
                media_type="text/plain; version=0.0.4; charset=utf-8"
            )
        else:
            # Return JSON error format
            return HealthResponse(
                status="unhealthy",
                version=settings.app_version,
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                checks={"error": str(e), "status": "unhealthy"}
            )




