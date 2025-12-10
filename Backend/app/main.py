# app/main.py

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

from app.core.config import settings  
from app.core.logger import logger, log_startup, log_shutdown, log_error
from app.core.postgres import db_manager
from app.models.schemas import ErrorResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup & shutdown."""
    log_startup(settings.app_name)

    # Connect to PostgreSQL (Main Brain) - Optional
    postgres_connected = False
    postgres_error = None
    try:
        await db_manager.connect()
        logger.info("✅ PostgreSQL: Connected successfully")
        postgres_connected = True
    except Exception as e:
        postgres_error = str(e)
        logger.warning(f"⚠️ PostgreSQL not available: {e}")
        logger.warning("Running without PostgreSQL - Limited functionality available")

    # Check Redis connection - Optional
    redis_connected = False
    redis_error = None
    try:
        import redis
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_password = os.getenv('REDIS_PASSWORD', 'nlpforge_redis_secure_password_2024')
        redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            password=redis_password,
            decode_responses=True
        )
        redis_client.ping()
        redis_connected = True
        logger.info("✅ Redis: Connected successfully")
    except Exception as e:
        redis_error = str(e)
        logger.warning(f"⚠️ Redis not available: {e}")
        logger.warning("Running without Redis - Vector search features disabled")

    app.state.startup_time = datetime.now(timezone.utc)
    app.state.request_count = 0
    app.state.postgres_connected = postgres_connected
    app.state.postgres_error = postgres_error
    app.state.redis_connected = redis_connected
    app.state.redis_error = redis_error

    logger.info("✅ Application startup completed")

    yield

    # Shutdown
    log_shutdown(settings.app_name)
    if postgres_connected:
        try:
            await db_manager.disconnect()
            logger.info("PostgreSQL: Main brain disconnected")
        except Exception as e:
            log_error(e, "PostgreSQL shutdown")
    logger.info("Application shutdown completed")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.description,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # CORS configuration - MUST be added FIRST before other middleware
    # Include both localhost and 127.0.0.1 variants, plus IPv6 localhost
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,http://[::1]:3000").split(",")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Initialize rate limiter with Redis storage (or fallback to memory)
    redis_password = os.getenv('REDIS_PASSWORD', '')
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = os.getenv('REDIS_PORT', '6379')
    
    # Build Redis URI with optional password
    if redis_password:
        storage_uri = f"redis://:{redis_password}@{redis_host}:{redis_port}/1"
    else:
        storage_uri = f"redis://{redis_host}:{redis_port}/1"
    
    # Try Redis, fallback to memory if Redis unavailable
    try:
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=storage_uri,
            default_limits=["1000/hour"],  # Default limit for all endpoints
            headers_enabled=True
        )
        logger.info("✅ Rate limiter: Using Redis storage")
    except Exception as e:
        logger.warning(f"⚠️ Rate limiter: Redis unavailable ({e}), using memory storage")
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["1000/hour"],
            headers_enabled=True
        )
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Create health router for v1
    health_router = APIRouter()
    
    @health_router.get("/health")
    async def health_check():
        """Comprehensive health check endpoint with service status and dependencies"""
        # Calculate uptime
        uptime = (datetime.now(timezone.utc) - app.state.startup_time).total_seconds()
        
        # Database check
        db_status = "healthy" if app.state.postgres_connected else "unhealthy"
        db_check = {
            "status": db_status,
            "message": "Database operational" if app.state.postgres_connected else "Database connection failed",
            "error": app.state.postgres_error if not app.state.postgres_connected else None,
            "critical": True,  # Database is critical for core functionality
            "impact": None if app.state.postgres_connected else "Authentication, templates, and data persistence unavailable"
        }
        
        # Redis check
        redis_status = "healthy" if app.state.redis_connected else "degraded"
        redis_check = {
            "status": redis_status,
            "message": "Redis operational" if app.state.redis_connected else "Redis connection failed",
            "error": app.state.redis_error if not app.state.redis_connected else None,
            "critical": False,  # Redis is optional
            "impact": None if app.state.redis_connected else "Vector search and caching features disabled"
        }
        
        # Determine overall status
        # healthy: all services up
        # degraded: non-critical services down
        # unhealthy: critical services down
        if not app.state.postgres_connected:
            overall_status = "unhealthy"
        elif not app.state.redis_connected:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "environment": settings.environment,
            "checks": {
                "database": db_check,
                "redis": redis_check
            },
            "metrics": {
                "uptime_seconds": uptime,
                "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
                "total_requests": app.state.request_count
            },
            "summary": {
                "services_total": 2,
                "services_healthy": sum([app.state.postgres_connected, app.state.redis_connected]),
                "services_critical_down": 1 if not app.state.postgres_connected else 0,
                "operational": app.state.postgres_connected
            }
        }
    
    @health_router.get("/health/postgres")
    async def postgres_health():
        """PostgreSQL specific health check"""
        if app.state.postgres_connected:
            return {
                "status": "connected",
                "message": "PostgreSQL is operational"
            }
        return JSONResponse(
            status_code=503,
            content={
                "status": "disconnected",
                "message": "PostgreSQL is not available",
                "error": app.state.postgres_error,
                "impact": "Authentication, templates, and data persistence unavailable"
            }
        )
    
    @health_router.get("/health/redis")
    async def redis_health():
        """Redis specific health check"""
        if app.state.redis_connected:
            return {
                "status": "connected",
                "message": "Redis is operational"
            }
        return JSONResponse(
            status_code=503,
            content={
                "status": "disconnected",
                "message": "Redis is not available",
                "error": app.state.redis_error,
                "impact": "Vector search and embedding features unavailable"
            }
        )

    # Import consolidated v1 router
    from app.api.v1 import router as v1_router
    
    # Mount health endpoints under /api/v1
    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    
    # Mount all v1 APIs under /api/v1
    app.include_router(v1_router, prefix="/api")

    @app.middleware("http")
    async def count_requests(request: Request, call_next):
        app.state.request_count += 1
        start = datetime.now(timezone.utc)
        
        # Set User Context
        from app.core.context_vars import user_id_ctx
        from app.core.security import verify_token
        
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
        user_id_token = user_id_ctx.set(None) # Reset context
        
        if token:
            try:
                payload = verify_token(token)
                user_id = payload.get("sub")
                if user_id:
                    user_id_ctx.set(user_id)
            except Exception:
                pass

        try:
            response = await call_next(request)
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            if settings.debug:
                # We don't want to log every request to the user feed, so we skip log_manager here
                # by NOT adding user_id to extra (or by filtering in handler)
                # But the standard logger will still pick it up for console
                logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)")
            return response
        finally:
            user_id_ctx.reset(user_id_token)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log_error(exc, f"Request: {request.method} {request.url}")
        
        # Ensure CORS headers are included in error responses
        response = JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                detail="An unexpected error occurred. Please try again later.",
                request_id=None
            ).model_dump()
        )
        
        # Add CORS headers manually for error responses
        origin = request.headers.get("origin")
        if origin and origin in cors_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response

    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs",
            "health": "/api/v1/dataset/list" 
        }

    @app.websocket("/ws/system-logs")
    async def websocket_endpoint(websocket: WebSocket, token: str = None):
        from app.core.log_manager import log_manager
        from app.core.security import verify_token
        from fastapi import Query
        
        logger.info(f"🔌 WebSocket connection attempt with token: {'present' if token else 'missing'}")
        
        # Accept connection first
        try:
            await websocket.accept()
            logger.info("✅ WebSocket connection accepted")
        except Exception as e:
            logger.error(f"❌ Failed to accept WebSocket connection: {e}")
            return
        
        # Authenticate
        user_id = None
        if token:
            try:
                payload = verify_token(token)
                user_id = payload.get("sub")
                logger.info(f"✅ WebSocket authenticated for user: {user_id}")
            except Exception as e:
                logger.error(f"❌ WebSocket token verification failed: {e}")
                try:
                    await websocket.send_json({
                        "error": "Authentication failed",
                        "detail": "Invalid or expired token"
                    })
                    await websocket.close(code=4001)
                except Exception:
                    pass
                return
        else:
            logger.warning("⚠️ WebSocket connection without token")
            try:
                await websocket.send_json({
                    "error": "Authentication required",
                    "detail": "Token parameter is required"
                })
                await websocket.close(code=4001)
            except Exception:
                pass
            return

        if not user_id:
            logger.error("❌ WebSocket: No user ID after token verification")
            try:
                await websocket.send_json({
                    "error": "Authentication failed",
                    "detail": "User ID not found in token"
                })
                await websocket.close(code=4001)
            except Exception:
                pass
            return

        # Connect to log manager
        await log_manager.connect(websocket, user_id)
        logger.info(f"✅ WebSocket connected to log manager for user: {user_id}")
        
        try:
            while True:
                # Keep connection alive by receiving messages
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info(f"🔌 WebSocket disconnected for user: {user_id}")
            log_manager.disconnect(websocket, user_id)
        except Exception as e:
            logger.error(f"❌ WebSocket error for user {user_id}: {e}")
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
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    main()