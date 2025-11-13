# app/main.py

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

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

    # Connect to PostgreSQL (Main Brain) - Optional
    postgres_connected = False
    try:
        await db_manager.connect()
        logger.info("PostgreSQL: Main brain connected (permanent storage)")
        postgres_connected = True
    except Exception as e:
        logger.warning(f"PostgreSQL not available: {e}")
        logger.warning("Running without PostgreSQL - using memory-only storage")

    # Load API templates into memory
    logger.info("Loading API templates...")
    template_service = get_template_service()
    
    # Try to load from database if connected
    templates = []
    if postgres_connected:
        try:
            templates = await template_service.load_all_templates()
        except Exception as e:
            logger.warning(f"Could not load templates from database: {e}")
    
    # If no templates in database, try to sync from JSON
    if not templates:
        logger.info("Loading templates from api_template.json...")
        backend_dir = Path(__file__).parent.parent
        json_path = backend_dir / "api_template.json"
        
        if json_path.exists():
            if postgres_connected:
                try:
                    stats = await template_service.sync_from_json(str(json_path))
                    logger.info(f"Synced {stats['loaded']} templates from JSON to database")
                    templates = await template_service.load_all_templates()
                except Exception as e:
                    logger.warning(f"Could not sync to database: {e}")
                    # Load directly to memory
                    import json
                    with open(json_path) as f:
                        json_templates = json.load(f)
                        template_service._templates = json_templates
                        templates = list(json_templates.values())
            else:
                # Load directly to memory without database
                import json
                with open(json_path) as f:
                    json_templates = json.load(f)
                    template_service._templates = json_templates
                    templates = list(json_templates.values())
                    logger.info(f"Loaded {len(templates)} templates to memory")
        else:
            logger.warning("api_template.json not found. Templates must be added via API.")
    
    cache_stats = template_service.get_cache_stats()
    logger.info(f"✅ Loaded {cache_stats['total_templates']} API templates")
    if cache_stats['intents']:
        logger.info(f"   Available APIs: {', '.join(cache_stats['intents'][:5])}{'...' if len(cache_stats['intents']) > 5 else ''}")

    # Load initial CSV dataset if it exists (only if Redis is empty)
    backend_dir = Path(__file__).parent.parent
    csv_dataset_path = backend_dir / "csv_dataset.csv"
    if csv_dataset_path.exists():
        try:
            # Check if Redis already has embeddings
            from app.nlp.embedding_manager import get_embedding_manager
            embedder = get_embedding_manager()
            stats = embedder.get_stats()
            existing_docs = stats.get('total_documents', 0)
            
            if existing_docs > 0:
                logger.info(f"✅ Redis already has {existing_docs} embeddings - skipping CSV load")
                logger.info(f"   Intents: {list(stats.get('intents', {}).keys())[:5]}")
            else:
                logger.info("📦 Loading initial CSV dataset into Redis (first time)...")
                from app.nlp.dataset_ingestor import ingest_csv_to_redis
                result = ingest_csv_to_redis(str(csv_dataset_path), clear_existing=False)
                if result.get("success"):
                    logger.info(f"✅ Loaded {result.get('count', 0)} embeddings from csv_dataset.csv")
                    logger.info(f"   New embeddings: {result.get('new_embeddings', 0)}, Skipped duplicates: {result.get('skipped_duplicates', 0)}")
                else:
                    logger.warning(f"Failed to load CSV dataset: {result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.warning(f"Could not load initial CSV dataset: {e}")
            logger.warning("Continuing without initial dataset - embeddings can be added via upload or generation")
    else:
        logger.info("No csv_dataset.csv found - embeddings will be added via upload or generation")

    app.state.startup_time = datetime.now(timezone.utc)
    app.state.request_count = 0
    app.state.template_service = template_service
    app.state.postgres_connected = postgres_connected

    logger.info("Application startup completed")

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

    # CORS configuration - restrict to specific origins in production
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if settings.environment == "development":
        cors_origins = ["*"]  # Allow all in development
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import enterprise routers
    from app.api.v1.auth import router as auth_router
    from app.api.v1.user_data import router as user_data_router
    from app.api.v1.embeddings import router as embeddings_router
    
    app.include_router(dataset_router, prefix="/api/v1/dataset", tags=["Dataset"])
    app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
    app.include_router(query_router, prefix="/api/v1", tags=["Query Processing"])
    app.include_router(templates_router, prefix="/api/v1", tags=["Template Management"])
    
    # Enterprise multi-tenant routes
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(user_data_router, prefix="/api/v1/user-data", tags=["User Data Management"])
    app.include_router(embeddings_router, prefix="/api/v1/embeddings", tags=["Vector Embeddings & Search"])

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