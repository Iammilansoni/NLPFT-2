# app/main.py

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings  
from app.core.logger import logger, log_startup, log_shutdown, log_error
from app.core.database import db_manager 
from app.api.v1.dataset import router as dataset_router
from app.api.v1.search import router as search_router
from app.models.schemas import ErrorResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup & shutdown."""
    log_startup(settings.app_name)

    try:
        settings.ensure_storage_directories()
        logger.info(f"Storage directory: {settings.storage_path}")

        await db_manager.connect()

        app.state.startup_time = datetime.now(timezone.utc)
        app.state.request_count = 0

        logger.info("Application startup completed")
    except Exception as e:
        log_error(e, "Application startup")
        raise

    yield

    # Shutdown
    log_shutdown(settings.app_name)
    try:
        await db_manager.disconnect()
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