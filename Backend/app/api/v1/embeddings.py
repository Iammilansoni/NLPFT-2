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
    
    ⏱️ RATE LIMIT: 30 embeddings per minute per IP
    
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
    redis_service: RedisVectorService = Depends(get_redis_vector_service)
):
    """
    Search for similar embeddings using vector similarity
    
    ⏱️ RATE LIMIT: 100 searches per minute per IP
    
    - Uses Redis vector search with HNSW index
    - Returns top-k most similar results
    - Filters by user and optionally by template
    """
    # Get user's preferred embedding model
    # Note: For search, we ideally want to search ALL indices or the one matching the query model
    # But for now, we'll use the user's preferred model to encode the query
    # TODO: Implement cross-index search or model detection
    
    # We need a DB session here to get settings, but this endpoint doesn't inject it
    # Let's add it
    pass 

    results = redis_service.search_similar(
        query=search_data.query,
        user_id=current_user.user_id,
        t_id=search_data.t_id,
        top_k=search_data.top_k,
        model_name=None # Will use default if not provided, or we should inject DB to get it
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
