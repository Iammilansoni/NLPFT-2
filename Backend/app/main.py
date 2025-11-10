# app/main.py

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings  
from app.core.logger import logger, log_startup, log_shutdown, log_error
from app.core.postgres import db_manager
from app.services.template_service import get_template_service
from app.api.v1.dataset import router as dataset_router
from app.api.v1.search import router as search_router
from app.api.v1.query import router as query_router
from app.api.v1.templates import router as templates_router
from app.models.schemas import ErrorResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup & shutdown."""
    log_startup(settings.app_name)

    try:
        # Connect to PostgreSQL (Main Brain)
        await db_manager.connect()
        logger.info("PostgreSQL: Main brain connected (permanent storage)")

        # Load API templates into memory
        logger.info("Loading API templates...")
        template_service = get_template_service()
        
        # First try to load from database
        templates = await template_service.load_all_templates()
        
        # If no templates in database, try to sync from JSON
        if not templates:
            logger.info("No templates in database, syncing from api_template.json...")
            backend_dir = Path(__file__).parent.parent
            json_path = backend_dir / "api_template.json"
            
            if json_path.exists():
                stats = await template_service.sync_from_json(str(json_path))
                logger.info(f"Synced {stats['loaded']} templates from JSON")
                templates = await template_service.load_all_templates()
            else:
                logger.warning("api_template.json not found. Templates must be added via API.")
        
        cache_stats = template_service.get_cache_stats()
        logger.info(f"✅ Loaded {cache_stats['total_templates']} API templates")
        logger.info(f"   Available APIs: {', '.join(cache_stats['intents'][:5])}{'...' if len(cache_stats['intents']) > 5 else ''}")

        app.state.startup_time = datetime.now(timezone.utc)
        app.state.request_count = 0
        app.state.template_service = template_service

        logger.info("Application startup completed")
    except Exception as e:
        log_error(e, "Application startup")
        raise

    yield

    # Shutdown
    log_shutdown(settings.app_name)
    try:
        await db_manager.disconnect()
        logger.info("PostgreSQL: Main brain disconnected")
        logger.info("Application shutdown completed")
    except Exception as e:
        log_error(e, "Application shutdown")

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(dataset_router, prefix="/api/v1/dataset", tags=["Dataset"])
    app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
    app.include_router(query_router, prefix="/api/v1", tags=["Query Processing"])
    app.include_router(templates_router, prefix="/api/v1", tags=["Template Management"])

    @app.middleware("http")
    async def count_requests(request: Request, call_next):
        app.state.request_count += 1
        start = datetime.now(timezone.utc)
        response = await call_next(request)
        duration = (datetime.now(timezone.utc) - start).total_seconds()
        if settings.debug:
            logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)")
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log_error(exc, f"Request: {request.method} {request.url}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                detail="An unexpected error occurred. Please try again later.",
                request_id=None
            ).model_dump()
        )

    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs",
            "health": "/api/v1/dataset/list" 
        }

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