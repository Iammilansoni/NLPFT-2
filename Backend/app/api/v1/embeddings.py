"""
Embeddings API endpoints
Handles vector embeddings stored in Redis with metadata in PostgreSQL
"""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid

from app.core.postgres import get_db
from app.services.enterprise_service import get_enterprise_service, EnterpriseService
from app.services.redis_vector_service import get_redis_vector_service, RedisVectorService
from app.api.v1.auth import get_current_user
from app.models.schemas import UserResponse, EmbeddingCreate, EmbeddingResponse, VectorSearchRequest, VectorSearchResult
from app.models.database_models import UserSettings
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


# =============================================================================
# EMBEDDING MODEL DISCOVERY & REGISTRATION
# =============================================================================

@router.get("/models/registered")
async def list_registered_models(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    include_dynamic: bool = True,
):
    """
    List all registered embedding models from the registry.
    
    Args:
        include_dynamic: Include dynamically registered models (default: True)
    """
    from app.core.embedding_model_registry import get_embedding_registry
    
    registry = get_embedding_registry()
    
    return {
        "models": registry.list_models(include_dynamic=include_dynamic),
        "default_model": registry.DEFAULT_MODEL_ID,
        "dynamic_count": len(registry.get_dynamic_models()),
    }


@router.post("/models/pull")
async def pull_embedding_model(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    model_name: str = Query(..., description="Ollama model name to pull"),
):
    """
    Pull an Ollama embedding model and register it.
    
    This is a synchronous operation that may take several minutes
    for large models. Consider using with appropriate timeouts.
    
    Args:
        model_name: Ollama model name to pull
    """
    from app.services.embedding_model_service import get_embedding_model_service
    import httpx
    
    service = get_embedding_model_service()
    
    try:
        # pull_and_register now returns EmbeddingModelSpec directly or raises
        spec = await service.pull_and_register(model_name)
        
        return {
            "model_id": spec.model_id,
            "dimension": spec.dimension,
            "display_name": spec.display_name,
            "redis_index": spec.redis_index_name,
            "status": "pulled_and_registered",
        }
    except httpx.ConnectError as e:
        # Ollama server not reachable
        logger.error(f"Cannot connect to Ollama server: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama server is not available. Please ensure the Ollama service is running.",
        )
    except OSError as e:
        # DNS resolution failures, network issues
        if "name resolution" in str(e).lower() or "Errno -3" in str(e):
            logger.error(f"Cannot resolve Ollama hostname: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot connect to Ollama server. Please ensure the Ollama service is running.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Network error: {str(e)}",
        )
    except RuntimeError as e:
        error_msg = str(e)
        # Provide clearer error messages
        if "name resolution" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ollama server is not available. Please ensure the Ollama service is running.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@router.get("/models/available")
async def list_available_embedding_models(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """
    List all available embedding models (Ollama + registered).
    
    Returns models with their:
    - Name and display name
    - Dimension (if known)
    - Local availability (pulled in Ollama)
    - Registration status in the system
    
    Use this endpoint to populate embedding model selection dropdowns.
    """
    from app.services.embedding_model_service import get_embedding_model_service
    
    service = get_embedding_model_service()
    
    try:
        models = await service.discover_ollama_models()
        
        return {
            "models": [m.to_dict() for m in models],
            "count": len(models),
            "local_count": sum(1 for m in models if m.is_local),
            "registered_count": sum(1 for m in models if m.is_registered),
        }
    except Exception as e:
        logger.error(f"Failed to list embedding models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {e}",
        )


@router.post("/models/detect-dimension")
async def detect_model_dimension(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    model_name: str = Query(..., description="Ollama model name"),
    auto_pull: bool = Query(True, description="Auto-pull if not available"),
):
    """
    Detect the embedding dimension for an Ollama model.
    
    This generates a test embedding and returns the dimension.
    Optionally pulls the model if not available locally.
    
    Args:
        model_name: Ollama model name (e.g., "nomic-embed-text")
        auto_pull: Whether to pull the model if not available
    """
    from app.services.ollama_embedding_service import get_ollama_service
    from app.core.embedding_model_registry import get_embedding_registry
    
    ollama = get_ollama_service()
    registry = get_embedding_registry()
    
    try:
        # Check if already registered
        if registry.is_valid_model(model_name):
            spec = registry.get_model(model_name)
            return {
                "model_name": model_name,
                "dimension": spec.dimension,
                "already_registered": True,
                "display_name": spec.display_name,
                "redis_index": spec.redis_index_name,
            }
        
        # Detect dimension
        dimension = await ollama.detect_dimension(model_name, auto_pull=auto_pull)
        
        if dimension is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not detect dimension for model: {model_name}. "
                       f"Make sure the model exists and is an embedding model.",
            )
        
        return {
            "model_name": model_name,
            "dimension": dimension,
            "already_registered": False,
            "message": f"Detected dimension: {dimension}. Call /models/register to register this model.",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting dimension: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/models/register")
async def register_embedding_model(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    model_name: str = Query(..., description="Ollama model name"),
    auto_pull: bool = Query(True, description="Auto-pull if not available"),
):
    """
    Register a new embedding model with auto-dimension detection.
    
    This:
    1. Pulls the model from Ollama if needed (auto_pull=True)
    2. Detects the embedding dimension automatically
    3. Registers the model in the EmbeddingModelRegistry
    4. Creates the Redis HNSW index for the model
    
    Args:
        model_name: Ollama model name (e.g., "mxbai-embed-large")
        auto_pull: Whether to pull the model if not available
    """
    from app.services.ollama_embedding_service import get_ollama_service
    from app.services.multi_model_redis_service import get_multi_model_redis_service
    
    ollama = get_ollama_service()
    
    try:
        success, result = await ollama.register_model_with_auto_dimension(
            model_name, 
            auto_pull=auto_pull
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Registration failed"),
            )
        
        # Ensure Redis index exists for the new model
        try:
            multi_redis = get_multi_model_redis_service()
            await multi_redis.ensure_index_exists(model_name)
            result["redis_index_created"] = True
        except Exception as redis_error:
            logger.warning(f"Could not create Redis index: {redis_error}")
            result["redis_index_created"] = False
            result["redis_index_error"] = str(redis_error)
        
        return {
            "success": True,
            **result,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/reembedding-impact")
async def check_reembedding_impact(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    new_model: str = Query(..., description="New embedding model to switch to"),
    db: AsyncSession = Depends(get_db),
):
    """
    Check impact of switching embedding models.
    
    Returns information about datasets that would need re-embedding
    if the user switches to a different embedding model.
    
    This is used to show warnings before model changes.
    """
    from sqlalchemy import select
    from app.models.database_models import Dataset, UserSettings
    from app.core.embedding_model_registry import get_embedding_registry
    
    registry = get_embedding_registry()
    
    # Get user's current model
    query_settings = await db.execute(
        select(UserSettings).where(UserSettings.u_id == current_user.u_id)
    )
    user_settings = query_settings.scalar_one_or_none()
    current_model = user_settings.default_embedding_model if user_settings else "nomic-embed-text"
    
    # If same model, no impact
    if current_model == new_model:
        return {
            "impact": "none",
            "message": "No change - same model",
            "affected_datasets": [],
            "reembedding_required": False,
        }
    
    # Find datasets with embeddings using current model
    query_datasets = await db.execute(
        select(Dataset).where(
            Dataset.u_id == current_user.u_id,
            Dataset.embedding_model == current_model,
            Dataset.embedded_rows > 0
        )
    )
    affected_datasets = query_datasets.scalars().all()
    
    # Calculate impact
    total_embeddings = sum(d.embedded_rows or 0 for d in affected_datasets)
    
    # Get dimension info
    try:
        current_spec = registry.get_model(current_model)
        current_dim = current_spec.dimension
    except ValueError:
        current_dim = None
    
    try:
        new_spec = registry.get_model(new_model)
        new_dim = new_spec.dimension
    except ValueError:
        new_dim = None
    
    if not affected_datasets:
        return {
            "impact": "none", 
            "message": "No existing embeddings to re-embed",
            "affected_datasets": [],
            "reembedding_required": False,
            "current_model": current_model,
            "new_model": new_model,
        }
    
    return {
        "impact": "high" if total_embeddings > 1000 else "medium" if total_embeddings > 100 else "low",
        "message": f"Switching from {current_model} to {new_model} will require re-embedding {len(affected_datasets)} datasets ({total_embeddings} total vectors)",
        "affected_datasets": [
            {
                "dataset_id": str(d.dataset_id),
                "name": d.name or d.csv_path.split('/')[-1] if d.csv_path else "Unknown",
                "embedding_count": d.embedded_rows,
                "embedding_model": d.embedding_model,
            }
            for d in affected_datasets
        ],
        "reembedding_required": True,
        "total_embeddings_affected": total_embeddings,
        "current_model": {
            "name": current_model,
            "dimension": current_dim,
        },
        "new_model": {
            "name": new_model,
            "dimension": new_dim,
        },
        "warning": "Embeddings from different models cannot be compared. "
                   "You must re-embed datasets to use them with the new model.",
    }
