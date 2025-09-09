"""Main FastAPI application for NLPForge."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import db_manager
from app.core.logger import logger, log_startup, log_shutdown, log_error
from app.api.v1 import health, dictionary, convert, metrics
from app.models.schemas import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    log_startup("NLPForge API")
    
    try:
        # Ensure storage directories exist
        settings.ensure_storage_directories()
        logger.info(f"✅ Storage directory initialized at: {settings.storage_path}")
        
        # Connect to database
        await db_manager.connect()
        
        # Initialize application state
        app.state.dictionary_loader = None  # Will be initialized when needed
        app.state.faiss_manager = None      # Will be initialized when needed
        app.state.embedding_model = None    # Will be initialized when needed
        app.state.last_worker_heartbeat = datetime.now(timezone.utc)
        app.state.startup_time = datetime.now(timezone.utc)
        app.state.request_count = 0
        
        logger.info("✅ Application startup completed")
        
    except Exception as e:
        log_error(e, "Application startup")
        raise
    
    yield
    
    # Shutdown
    log_shutdown("NLPForge API")
    try:
        await db_manager.disconnect()
        logger.info("✅ Application shutdown completed")
    except Exception as e:
        log_error(e, "Application shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A powerful NLP processing API with text conversion, dictionary management, and semantic analysis",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(dictionary.router, prefix="/api/v1")
    app.include_router(convert.router, prefix="/api/v1")
    app.include_router(metrics.router, prefix="/api/v1")
    
    # Middleware for request counting
    @app.middleware("http")
    async def count_requests(request: Request, call_next):  # type: ignore
        """Count all requests for metrics."""
        if hasattr(request.app.state, 'request_count'):
            request.app.state.request_count += 1
        
        start_time = datetime.now(timezone.utc)
        response = await call_next(request)
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Log request (optional, can be disabled in production)
        if settings.debug:
            logger.info(f"🌐 {request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)")  # type: ignore
        
        return response
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):  # type: ignore
        """Handle unexpected exceptions."""
        log_error(exc, f"Request: {request.method} {request.url}")
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                detail="An unexpected error occurred. Please try again later.",
                request_id=None
            ).model_dump()
        )
    
    # Root endpoint
    @app.get("/")
    async def root():  # type: ignore
        """Root endpoint with basic API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs",
            "health": "/api/v1/health"
        }
    
    return app


# Create the app instance
app = create_app()


def main():
    """Run the application."""
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
