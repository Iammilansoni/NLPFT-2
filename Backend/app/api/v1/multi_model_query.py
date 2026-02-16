# Backend\app\api\v1\multi_model_query.py

"""
Multi-Model Query API - Semantic Search with Model Governance

Purpose:
This API provides the main query endpoint for semantic search with
strict model governance. It enforces Settings as the source of truth
and prevents cross-model searches.

NON-NEGOTIABLE RULES:
1. Always use model from Settings
2. Check compatibility before search
3. Return clear errors on mismatch
4. Never silently fall back

Query Flow:
1. Pre-flight: Check model compatibility
2. Search: Use Settings model
3. Rerank: Model-agnostic scoring
4. Resolve: Fetch from PostgreSQL
5. Return: Clean JSON output
"""

from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import uuid

from app.core.postgres import get_db
from app.api.v1.auth import get_current_user
from app.models.schemas import UserResponse
from app.services.multi_model_semantic_service import get_multi_model_semantic_service
from app.services.multi_model_embedding_service import get_multi_model_embedding_service
from app.core.embedding_model_registry import get_embedding_registry


router = APIRouter(prefix="/query", tags=["multi-model-query"])


# =============================================================================
# SCHEMAS
# =============================================================================

class SemanticQueryRequest(BaseModel):
    """Semantic query request"""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    dataset_id: Optional[str] = Field(None, description="Optional dataset UUID filter")
    template_id: Optional[str] = Field(None, description="Optional template UUID filter")
    intent: Optional[str] = Field(None, description="Optional detected intent")
    include_alternatives: bool = Field(default=False, description="Include alternative APIs")


class FinalOutput(BaseModel):
    """Final API output (clean JSON)"""
    t_id: str
    api_name: str
    endpoint: str
    method: str
    confidence_score: float
    request_schema: Optional[dict] = None
    response_schema: Optional[dict] = None


class StageResult(BaseModel):
    """Stage result for visibility"""
    query: Optional[str] = None
    similarity_score: Optional[float] = None
    t_id: Optional[str] = None
    avg_similarity: Optional[float] = None
    final_score: Optional[float] = None
    rank: Optional[int] = None


class SemanticQueryResponse(BaseModel):
    """Complete semantic query response"""
    success: bool
    error: Optional[str] = None
    message: Optional[str] = None
    
    # Stage-by-stage visibility
    stage1_vector_search: Optional[List[dict]] = None
    stage2_reranking: Optional[List[dict]] = None
    final_output: Optional[FinalOutput] = None
    
    # Metadata
    metadata: Optional[dict] = None
    
    # Legacy fields
    api_name: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    confidence: Optional[float] = None


class ReembedRequest(BaseModel):
    """Re-embed request"""
    new_model_id: Optional[str] = Field(
        None, 
        description="New model to use (updates Settings)"
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/semantic-search", response_model=SemanticQueryResponse)
async def semantic_search(
    request: SemanticQueryRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Perform semantic search with model governance.
    
    ❗ IMPORTANT:
    - Uses embedding model from Settings (source of truth)
    - Validates model compatibility with dataset
    - Returns clear error if mismatch detected
    - Never silently uses wrong model
    
    Returns:
    - Stage 1: Vector search results
    - Stage 2: Re-ranked results
    - Final: Best matching API template
    """
    service = get_multi_model_semantic_service()
    
    # Parse optional UUIDs
    dataset_id = uuid.UUID(request.dataset_id) if request.dataset_id else None
    template_id = uuid.UUID(request.template_id) if request.template_id else None
    
    result = await service.semantic_search(
        db=db,
        user_id=current_user.u_id,
        user_query=request.query,
        top_k=request.top_k,
        dataset_id=dataset_id,
        template_id=template_id,
        user_query_intent=request.intent,
        include_alternatives=request.include_alternatives
    )
    
    return result


@router.post("/datasets/{dataset_id}/embed")
async def embed_dataset(
    dataset_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    force_reembed: bool = Query(False, description="Force re-embedding")
):
    """
    Embed a dataset using Settings model.
    
    ❗ Uses model from Settings (source of truth)
    
    Args:
        dataset_id: Dataset UUID
        force_reembed: If True, re-embed even if already done
        
    Returns:
        Embedding status with progress info
    """
    service = get_multi_model_embedding_service()
    
    result = await service.embed_dataset(
        db=db,
        user_id=current_user.u_id,
        dataset_id=dataset_id,
        force_reembed=force_reembed
    )
    
    return result


@router.post("/datasets/{dataset_id}/reembed")
async def reembed_dataset(
    dataset_id: uuid.UUID,
    request: ReembedRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Re-embed a dataset with a new model.
    
    ❗ This updates Settings if new_model_id provided
    
    Args:
        dataset_id: Dataset UUID
        new_model_id: Optional new model (updates Settings)
        
    Returns:
        Re-embedding status
    """
    service = get_multi_model_embedding_service()
    
    result = await service.reembed_dataset(
        db=db,
        user_id=current_user.u_id,
        dataset_id=dataset_id,
        new_model_id=request.new_model_id
    )
    
    return result


@router.get("/datasets/{dataset_id}/embedding-status")
async def get_embedding_status(
    dataset_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Get embedding status for a dataset.
    
    Returns:
        Embedding status with progress and model info
    """
    service = get_multi_model_embedding_service()
    
    result = await service.get_embedding_status(
        db=db,
        user_id=current_user.u_id,
        dataset_id=dataset_id
    )
    
    return result


@router.get("/models")
async def list_embedding_models(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    List all available embedding models.
    
    Returns:
        List of models with dimensions and capabilities
    """
    registry = get_embedding_registry()
    
    return {
        "models": registry.list_models(),
        "default_model": registry.DEFAULT_MODEL_ID,
        "count": len(registry.list_model_ids())
    }


@router.get("/health")
async def query_service_health(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Check query service health.
    
    Returns:
        Health status of all components
    """
    from app.services.multi_model_redis_service import get_multi_model_redis_service
    
    redis_service = get_multi_model_redis_service()
    redis_health = redis_service.health_check()
    
    return {
        "status": redis_health.get("status", "unknown"),
        "redis": redis_health.get("redis", "unknown"),
        "indexes": redis_health.get("indexes", {})
    }