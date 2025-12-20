"""
Embeddings API endpoints
Handles vector embeddings stored in Redis with metadata in PostgreSQL
"""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid

from app.core.postgres import get_db
from app.services.enterprise_service import get_enterprise_service, EnterpriseService
from app.services.redis_vector_service import get_redis_vector_service, RedisVectorService
from app.api.v1.auth import get_current_user
from app.models.schemas import UserResponse, EmbeddingCreate, EmbeddingResponse, VectorSearchRequest, VectorSearchResult
from app.core.logger import logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# Schemas imported from app.models.schemas


@router.post("/create", response_model=EmbeddingResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_embedding(
    request: Request,
    embedding_data: EmbeddingCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    enterprise_service: EnterpriseService = Depends(get_enterprise_service),
    redis_service: RedisVectorService = Depends(get_redis_vector_service)
):
    """
    Create a new embedding
    
    RATE LIMIT: 30 embeddings per minute per IP
    
    - Generates vector embedding using sentence-transformers
    - Stores vector in Redis for fast search
    - Stores metadata in PostgreSQL for tracking
    """
    # Get user's preferred embedding model
    query_settings = await db.execute(
        select(UserSettings).where(UserSettings.u_id == current_user.u_id)
    )
    user_settings = query_settings.scalar_one_or_none()
    model_name = user_settings.default_embedding_model if user_settings else None

    # Store vector in Redis
    redis_key, vector = redis_service.store_embedding(
        user_id=current_user.user_id,
        query=embedding_data.query,
        t_id=embedding_data.t_id,
        csv_id=embedding_data.csv_id,
        model_name=model_name
    )
    
    # Store metadata in PostgreSQL
    embedding = await enterprise_service.create_embedding_metadata(
        db=db,
        user_id=current_user.user_id,
        redis_key=redis_key,
        t_id=embedding_data.t_id,
        csv_id=embedding_data.csv_id,
        model_name=model_name or "default"
    )
    
    return EmbeddingResponse(
        emb_id=embedding.emb_id,
        user_id=embedding.user_id,
        t_id=embedding.t_id,
        csv_id=embedding.csv_id,
        redis_key=embedding.redis_key,
        query=embedding_data.query
    )


@router.post("/search", response_model=List[VectorSearchResult])
@limiter.limit("100/minute")
async def search_embeddings(
    request: Request,
    search_data: VectorSearchRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    redis_service: RedisVectorService = Depends(get_redis_vector_service)
):
    """
    Search for similar embeddings using vector similarity
    
    RATE LIMIT: 100 searches per minute per IP
    
    - Uses Redis vector search with HNSW index
    - Returns top-k most similar results
    - Filters by user and optionally by template
    - Detects and warns about embedding model mismatches
    """
    from sqlalchemy import select
    from app.models.database_models import UserSettings, Dataset
    from app.core.models_config import validate_model_compatibility, DEFAULT_EMBEDDING_MODEL
    
    # Get user's preferred embedding model from settings
    query_settings = await db.execute(
        select(UserSettings).where(UserSettings.u_id == current_user.user_id)
    )
    user_settings = query_settings.scalar_one_or_none()
    search_model = user_settings.default_embedding_model if user_settings else DEFAULT_EMBEDDING_MODEL
    
    # Check for model mismatch if searching within a specific template/dataset
    model_mismatch_warning = None
    if search_data.t_id:
        # Try to get the dataset's embedding model
        try:
            query_dataset = await db.execute(
                select(Dataset).where(
                    Dataset.t_id == search_data.t_id,
                    Dataset.u_id == current_user.user_id
                ).order_by(Dataset.created_at.desc()).limit(1)
            )
            dataset = query_dataset.scalar_one_or_none()
            
            if dataset and dataset.embedding_model:
                compatibility = validate_model_compatibility(
                    dataset_model=dataset.embedding_model,
                    search_model=search_model
                )
                if not compatibility.get("compatible", True):
                    model_mismatch_warning = compatibility
                    logger.warning(
                        f"Model mismatch detected: dataset={dataset.embedding_model}, "
                        f"search={search_model} for template {search_data.t_id}"
                    )
        except Exception as e:
            logger.warning(f"Could not check model compatibility: {e}")

    results = redis_service.search_similar(
        query=search_data.query,
        user_id=current_user.user_id,
        t_id=search_data.t_id,
        top_k=search_data.top_k,
        model_name=search_model
    )
    
    # Convert to response format
    search_results = []
    for result in results:
        search_results.append(VectorSearchResult(
            redis_key=result.get("redis_key", ""),
            query=result.get("query", ""),
            similarity_score=float(result.get("__vector_score", 0.0)),
            user_id=result.get("user_id", ""),
            t_id=result.get("t_id") if result.get("t_id") else None,
            csv_id=result.get("csv_id") if result.get("csv_id") else None
        ))
    
    # If there's a mismatch warning, we need to return it
    # For now, log it - the frontend checks via /check-compatibility endpoint
    if model_mismatch_warning:
        logger.info(f"Returning {len(search_results)} results with model mismatch warning")
    
    return search_results



@router.get("/count")
async def count_embeddings(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    redis_service: RedisVectorService = Depends(get_redis_vector_service),
    t_id: Optional[uuid.UUID] = Query(None)
):
    """
    Count embeddings for current user
    
    Optionally filter by template
    """
    count = redis_service.count_embeddings(
        user_id=current_user.user_id,
        t_id=t_id
    )
    
    return {
        "user_id": current_user.user_id,
        "t_id": t_id,
        "count": count
    }


@router.delete("/{redis_key}")
async def delete_embedding(
    redis_key: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    enterprise_service: EnterpriseService = Depends(get_enterprise_service),
    redis_service: RedisVectorService = Depends(get_redis_vector_service)
):
    """
    Delete an embedding
    
    - Removes vector from Redis
    - Removes metadata from PostgreSQL
    """
    # Verify ownership by checking if redis_key starts with user's ID
    if not redis_key.startswith(f"embedding:{current_user.user_id}:"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this embedding"
        )
    
    # Delete from Redis
    redis_deleted = redis_service.delete_embedding(redis_key)
    
    # Delete metadata from PostgreSQL
    pg_deleted = await enterprise_service.delete_embedding_by_redis_key(
        db=db,
        redis_key=redis_key,
        user_id=current_user.user_id
    )
    
    return {
        "redis_key": redis_key,
        "deleted_from_redis": redis_deleted,
        "deleted_from_postgres": pg_deleted
    }


@router.delete("/template/{template_id}")
async def delete_template_embeddings(
    template_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    enterprise_service: EnterpriseService = Depends(get_enterprise_service),
    redis_service: RedisVectorService = Depends(get_redis_vector_service)
):
    """
    Delete all embeddings for a template
    
    - Removes all vectors from Redis
    - Removes all metadata from PostgreSQL
    """
    # Verify template ownership
    template = await enterprise_service.get_template_by_id(
        db=db,
        template_id=template_id,
        user_id=current_user.user_id
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Delete from Redis
    redis_count = redis_service.delete_template_embeddings(
        user_id=current_user.user_id,
        template_id=template_id
    )
    
    # Delete metadata from PostgreSQL
    pg_count = await enterprise_service.delete_embeddings_by_template(
        db=db,
        template_id=template_id,
        user_id=current_user.user_id
    )
    
    return {
        "template_id": template_id,
        "deleted_from_redis": redis_count,
        "deleted_from_postgres": pg_count
    }


@router.get("/check-compatibility")
async def check_model_compatibility(
    dataset_id: Optional[uuid.UUID] = Query(None),
    template_id: Optional[uuid.UUID] = Query(None),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if user's current embedding model is compatible with a dataset's embeddings.
    
    Returns compatibility info and suggestions if mismatch is detected.
    
    Args:
        dataset_id: Optional dataset UUID to check
        template_id: Optional template UUID (gets latest dataset for template)
    
    Returns:
        Compatibility status with model details and recommended actions
    """
    from sqlalchemy import select
    from app.models.database_models import UserSettings, Dataset
    from app.core.models_config import (
        validate_model_compatibility, 
        DEFAULT_EMBEDDING_MODEL,
        get_embedding_model_info,
        MODEL_DIMENSIONS
    )
    
    # Get user UUID from User model (u_id attribute)
    user_uuid = current_user.u_id
    
    # Get user's current settings
    query_settings = await db.execute(
        select(UserSettings).where(UserSettings.u_id == user_uuid)
    )
    user_settings = query_settings.scalar_one_or_none()
    current_model = user_settings.default_embedding_model if user_settings else DEFAULT_EMBEDDING_MODEL
    
    # Get dataset's embedding model
    dataset_model = None
    dataset_info = None
    
    if dataset_id:
        query_dataset = await db.execute(
            select(Dataset).where(
                Dataset.d_id == dataset_id,
                Dataset.u_id == user_uuid
            )
        )
        dataset = query_dataset.scalar_one_or_none()
        if dataset:
            dataset_model = dataset.embedding_model
            dataset_info = {
                "dataset_id": str(dataset.d_id),
                "name": dataset.file_name,
                "embedding_model": dataset.embedding_model
            }
    elif template_id:
        query_dataset = await db.execute(
            select(Dataset).where(
                Dataset.t_id == template_id,
                Dataset.u_id == user_uuid
            ).order_by(Dataset.created_at.desc()).limit(1)
        )
        dataset = query_dataset.scalar_one_or_none()
        if dataset:
            dataset_model = dataset.embedding_model
            dataset_info = {
                "dataset_id": str(dataset.d_id),
                "name": dataset.file_name,
                "embedding_model": dataset.embedding_model
            }
    
    # If no dataset found or no embedding model recorded
    if not dataset_model:
        return {
            "compatible": True,
            "current_model": current_model,
            "current_dimension": MODEL_DIMENSIONS.get(current_model, 768),
            "dataset_model": None,
            "message": "No dataset embeddings found to compare"
        }
    
    # Check compatibility
    compatibility = validate_model_compatibility(
        dataset_model=dataset_model,
        search_model=current_model
    )
    
    # Enhance with model info
    try:
        current_model_info = get_embedding_model_info(current_model)
        compatibility["current_model_info"] = {
            "display_name": current_model_info.display_name,
            "dimension": current_model_info.dimension,
            "speed": current_model_info.speed.value
        }
    except ValueError as e:
        logger.debug(f"Could not get current model info: {e}")
    
    try:
        if dataset_model:
            dataset_model_info = get_embedding_model_info(dataset_model)
            compatibility["dataset_model_info"] = {
                "display_name": dataset_model_info.display_name,
                "dimension": dataset_model_info.dimension,
                "speed": dataset_model_info.speed.value
            }
    except ValueError as e:
        logger.debug(f"Could not get dataset model info: {e}")
    
    if dataset_info:
        compatibility["dataset"] = dataset_info
    
    return compatibility


@router.get("/health")
async def embeddings_health(
    redis_service: RedisVectorService = Depends(get_redis_vector_service)
):
    """Check embeddings service health"""
    redis_healthy = redis_service.health_check()
    
    return {
        "status": "healthy" if redis_healthy else "unhealthy",
        "redis": "connected" if redis_healthy else "disconnected",
        "vector_dimension": redis_service.vector_dimension,
        "index_name": redis_service.index_name
    }

