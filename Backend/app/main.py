# app/main.py
"""
NLPForge FastAPI Application Entry Point.

Middleware order (Starlette processes outer-to-inner for requests,
inner-to-outer for responses):

    1. CORSMiddleware          — must be outermost so preflight passes first
    2. TracingMiddleware        — injects request_id / trace_id into context
    3. SecurityHeadersMiddleware — attaches CSP / HSTS headers
    4. SlowAPI rate limiter     — applied per-route via decorator
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import APIRouter, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, settings
from app.core.context_vars import request_id_ctx, trace_id_ctx
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ErrorCategory,
    ErrorCode,
    ExternalServiceError,
    InternalError,
    NLPForgeError,
    NotFoundError,
    RateLimitError,
    RedisError,
)
from app.core.exceptions import (
    ValidationError as NLPValidationError,
)
from app.core.logger import log_error, log_event, log_shutdown, log_startup, logger
from app.core.postgres import db_manager
from app.core.tracing import TracingMiddleware
from app.models.schemas.common_schemas import ErrorDetail, ErrorResponse, make_error_response

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_trace_headers(request: Request) -> dict:
    return {
        "request_id": request_id_ctx.get(),
        "trace_id":   trace_id_ctx.get(),
    }


def _error_json_response(
    request: Request,
    status_code: int,
    code: str,
    category: str,
    user_message: str,
    developer_message: str | None = None,
    recovery_suggestions: list[str] | None = None,
    cors_origins: list[str] | None = None,
) -> JSONResponse:
    """Build a CORS-safe JSONResponse with the standard ErrorResponse envelope."""
    ids = _get_trace_headers(request)
    body = ErrorResponse(
        error=ErrorDetail(
            code=code,
            category=category,
            request_id=ids.get("request_id"),
            trace_id=ids.get("trace_id"),
            user_message=user_message,
            developer_message=developer_message if not settings.environment == "production" else None,
            recovery_suggestions=recovery_suggestions or [],
        )
    )
    response = JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))

    # Manually re-inject CORS headers (CORS middleware doesn't process error paths)
    origin = request.headers.get("origin")
    if origin and cors_origins and origin in cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup & shutdown."""
    log_startup(settings.app_name)

    # PostgreSQL
    postgres_connected = False
    postgres_error = None
    try:
        await db_manager.connect()
        logger.info("PostgreSQL connected successfully",
                    extra={"extra": {"event_name": "db_connect", "database": "postgres", "status": "success"}})
        postgres_connected = True
    except Exception as exc:
        postgres_error = str(exc)
        logger.error(
            f"PostgreSQL connection failed: {type(exc).__name__}",
            extra={"extra": {
                "event_name": "db_connect",
                "database": "postgres",
                "status": "failed",
                "failure_cause": str(exc),
                "recovery_action": "Check POSTGRES_* env vars and DB container health",
            }},
        )

    # Encryption
    encryption_configured = False
    try:
        from app.core.encryption import is_encryption_configured
        encryption_configured = is_encryption_configured()
        if encryption_configured:
            logger.info("API key encryption configured",
                        extra={"extra": {"event_name": "encryption_check", "status": "configured"}})
        else:
            logger.warning(
                "SECRET_KEY_ENCRYPTION not set — LLM provider API keys cannot be stored securely",
                extra={"extra": {
                    "event_name": "encryption_check",
                    "status": "not_configured",
                    "suggested_fix": "Set SECRET_KEY_ENCRYPTION in Backend/.env",
                }},
            )
    except Exception as exc:
        logger.warning(f"Encryption check failed: {type(exc).__name__}: {exc}")

    app.state.encryption_configured = encryption_configured

    # Redis
    redis_connected = False
    redis_error = None
    try:
        import redis as redis_lib
        redis_client = redis_lib.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True,
        )
        redis_client.ping()
        redis_connected = True
        logger.info("Redis connected successfully",
                    extra={"extra": {"event_name": "redis_connect", "status": "success"}})
    except Exception as exc:
        redis_error = str(exc)
        logger.warning(
            f"Redis not available: {type(exc).__name__}",
            extra={"extra": {
                "event_name": "redis_connect",
                "status": "failed",
                "failure_cause": str(exc),
                "recovery_action": "Vector search features will be disabled until Redis is available",
            }},
        )

    app.state.startup_time       = datetime.now(timezone.utc)
    app.state.request_count      = 0
    app.state.postgres_connected = postgres_connected
    app.state.postgres_error     = postgres_error
    app.state.redis_connected    = redis_connected
    app.state.redis_error        = redis_error

    # Auto-register Ollama embedding models
    try:
        from app.services.embedding_model_service import auto_register_local_embedding_models
        result = await auto_register_local_embedding_models()
        if result.get("registered"):
            logger.info(
                f"Auto-registered {len(result['registered'])} embedding model(s)",
                extra={"extra": {"event_name": "embedding_auto_register", "models": result["registered"]}},
            )
    except Exception as exc:
        logger.warning(f"Could not auto-register embedding models: {type(exc).__name__}: {exc}")

    # Recover stale embedding tasks
    if postgres_connected:
        try:
            from app.services.stale_task_recovery import recover_stale_embedding_tasks
            recovered = await recover_stale_embedding_tasks()
            if recovered > 0:
                logger.info(
                    f"Recovered {recovered} stale embedding task(s)",
                    extra={"extra": {"event_name": "stale_task_recovery", "count": recovered}},
                )
        except Exception as exc:
            logger.warning(f"Stale task recovery failed: {type(exc).__name__}: {exc}")

    log_event(
        "application_startup_complete",
        category="infrastructure",
        level="INFO",
        output_result={
            "postgres": "connected" if postgres_connected else "unavailable",
            "redis": "connected" if redis_connected else "unavailable",
            "encryption": "configured" if encryption_configured else "not_configured",
        },
    )

    yield

    # ── Shutdown ──
    log_shutdown(settings.app_name)
    if postgres_connected:
        try:
            await db_manager.disconnect()
            logger.info("PostgreSQL disconnected gracefully")
        except Exception as exc:
            logger.exception(f"Error during PostgreSQL shutdown: {exc}")
    log_event("application_shutdown_complete", category="infrastructure", level="INFO")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.description,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS (must be outermost) ──────────────────────────────────────────
    cors_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://localhost:19000,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:19000,"
        "http://[::1]:3000",
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Trace-ID", "X-Correlation-ID", "*"],
    )

    # ── Tracing (request_id / trace_id / correlation_id) ─────────────────
    app.add_middleware(TracingMiddleware, service_name="nlpforge-backend")

    # ── Security headers ──────────────────────────────────────────────────
    from starlette.middleware.base import BaseHTTPMiddleware

    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"]  = "nosniff"
            response.headers["X-Frame-Options"]         = "DENY"
            response.headers["X-XSS-Protection"]        = "0"
            response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"

            if settings.environment == "production":
                csp = (
                    "default-src 'self'; "
                    "script-src 'self'; "
                    "style-src 'self'; "
                    "img-src 'self' data: blob:; "
                    "font-src 'self' data:; "
                    "connect-src 'self' wss:; "
                    "frame-ancestors 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self'"
                )
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            else:
                csp = (
                    "default-src 'self'; "
                    "script-src 'self'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: blob:; "
                    "font-src 'self' data:; "
                    "connect-src 'self' ws: wss: http://localhost:* http://127.0.0.1:* http://10.0.0.1:*;"
                )
            response.headers["Content-Security-Policy"] = csp
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # ── Rate limiter ──────────────────────────────────────────────────────
    if REDIS_PASSWORD:
        storage_uri = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1"
    else:
        storage_uri = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"

    try:
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=storage_uri,
            default_limits=["1000/hour"],
            headers_enabled=True,
        )
        logger.info("Rate limiter: using Redis storage")
    except Exception as exc:
        logger.warning(f"Rate limiter Redis unavailable ({exc}), falling back to memory storage")
        limiter = Limiter(key_func=get_remote_address, default_limits=["1000/hour"], headers_enabled=True)

    app.state.limiter = limiter

    # ── Exception handlers ────────────────────────────────────────────────

    @app.exception_handler(NLPForgeError)
    async def nlpforge_exception_handler(request: Request, exc: NLPForgeError):
        """Handle all application-level NLPForgeError subclasses."""
        log_level = "WARNING" if exc.http_status < 500 else "ERROR"
        logger.log(
            __import__("logging").getLevelName(log_level),
            f"application_error code={exc.code} status={exc.http_status}",
            extra={"extra": {
                "event_name": "application_error",
                "error_code": exc.code,
                "error_category": exc.category,
                "http_status": exc.http_status,
                "developer_message": exc.developer_message,
                **exc.extra,
            }},
        )
        return _error_json_response(
            request,
            exc.http_status,
            exc.code,
            exc.category,
            exc.user_message,
            exc.developer_message,
            exc.recovery_suggestions,
            cors_origins,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Convert Pydantic validation errors into standard 422 responses."""
        errors = exc.errors()
        logger.warning(
            f"request_validation_error path={request.url.path} errors={len(errors)}",
            extra={"extra": {
                "event_name": "request_validation_error",
                "path": request.url.path,
                "method": request.method,
                "errors": errors,
            }},
        )
        ids = _get_trace_headers(request)
        body = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.VALIDATION_FAILED,
                category=ErrorCategory.VALIDATION,
                request_id=ids.get("request_id"),
                trace_id=ids.get("trace_id"),
                user_message="The request contained invalid data. Please check your input.",
                developer_message=str(errors),
                recovery_suggestions=["Review the request schema", "Check required fields and data types"],
            )
        )
        response = JSONResponse(status_code=422, content=body.model_dump(mode="json"))
        origin = request.headers.get("origin")
        if origin and origin in cors_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """SlowAPI rate limit exceeded — return structured 429."""
        logger.warning(
            f"rate_limit_exceeded path={request.url.path}",
            extra={"extra": {
                "event_name": "rate_limit_exceeded",
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            }},
        )
        return _error_json_response(
            request, 429,
            ErrorCode.RATE_LIMIT_EXCEEDED,
            ErrorCategory.RATE_LIMIT,
            "Too many requests. Please slow down and try again shortly.",
            recovery_suggestions=["Wait before retrying", "Reduce request frequency"],
            cors_origins=cors_origins,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Last-resort handler for any unhandled exception."""
        logger.exception(
            f"unhandled_exception {type(exc).__name__} on {request.method} {request.url.path}",
            extra={"extra": {
                "event_name": "unhandled_exception",
                "error_type": type(exc).__name__,
                "method": request.method,
                "path": str(request.url.path),
                "failure_cause": str(exc),
                "recovery_action": "Investigate traceback above",
            }},
        )
        return _error_json_response(
            request, 500,
            ErrorCode.INTERNAL_ERROR,
            ErrorCategory.INTERNAL,
            "An unexpected error occurred. Our team has been notified. Please try again.",
            developer_message=f"{type(exc).__name__}: {exc}",
            recovery_suggestions=["Retry the request", "Contact support with the request_id"],
            cors_origins=cors_origins,
        )

    # ── Request counter middleware (lightweight) ──────────────────────────
    @app.middleware("http")
    async def count_requests(request: Request, call_next):
        app.state.request_count += 1
        return await call_next(request)

    # ── Health endpoints ──────────────────────────────────────────────────
    health_router = APIRouter()

    @health_router.get("/health")
    async def health_check():
        """Comprehensive health check endpoint."""
        uptime = (datetime.now(timezone.utc) - app.state.startup_time).total_seconds()
        db_ok  = app.state.postgres_connected
        rd_ok  = app.state.redis_connected

        overall = "healthy" if db_ok and rd_ok else ("degraded" if db_ok else "unhealthy")
        return {
            "status": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": settings.app_version,
            "environment": settings.environment,
            "checks": {
                "database": {
                    "status": "healthy" if db_ok else "unhealthy",
                    "message": "PostgreSQL operational" if db_ok else "PostgreSQL unavailable",
                    "error": app.state.postgres_error if not db_ok else None,
                    "critical": True,
                },
                "redis": {
                    "status": "healthy" if rd_ok else "degraded",
                    "message": "Redis operational" if rd_ok else "Redis unavailable",
                    "error": app.state.redis_error if not rd_ok else None,
                    "critical": False,
                },
            },
            "metrics": {
                "uptime_seconds": uptime,
                "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
                "total_requests": app.state.request_count,
            },
            "summary": {
                "services_total": 2,
                "services_healthy": sum([db_ok, rd_ok]),
                "services_critical_down": 0 if db_ok else 1,
                "operational": db_ok,
            },
        }

    @health_router.get("/health/postgres")
    async def postgres_health():
        if app.state.postgres_connected:
            return {"status": "connected", "message": "PostgreSQL is operational"}
        return JSONResponse(status_code=503, content={
            "status": "disconnected",
            "message": "PostgreSQL is not available",
            "error": app.state.postgres_error,
            "impact": "Authentication, templates, and data persistence unavailable",
        })

    @health_router.get("/health/redis")
    async def redis_health():
        if app.state.redis_connected:
            return {"status": "connected", "message": "Redis is operational"}
        return JSONResponse(status_code=503, content={
            "status": "disconnected",
            "message": "Redis is not available",
            "error": app.state.redis_error,
            "impact": "Vector search and embedding features unavailable",
        })

    app.include_router(health_router, prefix="/api/v1", tags=["Health"])

    # ── Metrics (Prometheus) ──────────────────────────────────────────────
    from app.core.metrics import metrics_router
    app.include_router(metrics_router, prefix="/api/v1")

    # ── API routes ────────────────────────────────────────────────────────
    from app.api.v1 import router as v1_router
    app.include_router(v1_router, prefix="/api")

    # ── Root ──────────────────────────────────────────────────────────────
    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    # ── WebSocket: system log stream ──────────────────────────────────────
    @app.websocket("/ws/system-logs")
    async def websocket_endpoint(websocket: WebSocket, token: str = None):
        from app.core.log_manager import log_manager
        from app.core.security import verify_token

        logger.debug("WebSocket connection attempt", extra={"extra": {
            "event_name": "ws_connect_attempt", "token_present": bool(token),
        }})

        try:
            await websocket.accept()
        except Exception as exc:
            logger.error(f"WebSocket accept failed: {exc}")
            return

        if not token:
            logger.warning("WebSocket rejected — no token provided")
            try:
                await websocket.send_json({"error": "Authentication required", "detail": "Token is required"})
                await websocket.close(code=4001)
            except Exception:
                pass
            return

        user_id = None
        try:
            payload  = verify_token(token)
            user_id  = payload.get("sub")
        except Exception as exc:
            logger.warning(f"WebSocket token verification failed: {type(exc).__name__}")
            try:
                await websocket.send_json({"error": "Authentication failed", "detail": "Invalid or expired token"})
                await websocket.close(code=4001)
            except Exception:
                pass
            return

        if not user_id:
            logger.error("WebSocket: user_id missing from token payload")
            try:
                await websocket.send_json({"error": "Authentication failed", "detail": "User ID not found in token"})
                await websocket.close(code=4001)
            except Exception:
                pass
            return

        await log_manager.connect(websocket, user_id)
        logger.info("WebSocket connected", extra={"extra": {"event_name": "ws_connected"}})

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected", extra={"extra": {"event_name": "ws_disconnected"}})
            log_manager.disconnect(websocket, user_id)
        except Exception as exc:
            logger.error(f"WebSocket error: {exc}", extra={"extra": {"event_name": "ws_error", "error": str(exc)}})
            log_manager.disconnect(websocket, user_id)

    return app


app = create_app()


def main():
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()