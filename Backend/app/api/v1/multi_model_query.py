# Backend\app\api\v1\multi_model_query.py

"""
Query API - natural language -> API template + extracted request body.

POST /api/v1/query/semantic-search is the product's main endpoint. See
app/services/multi_model_semantic_service.py for the three-stage pipeline.
"""

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.embedding_model_registry import get_embedding_registry
from app.core.postgres import get_db
from app.core.rate_limit import limiter
from app.models.schemas import UserResponse
from app.nlp.cross_encoder_reranker import STAGE1_TOP_K
from app.services.multi_model_embedding_service import get_multi_model_embedding_service
from app.services.multi_model_semantic_service import get_multi_model_semantic_service

router = APIRouter(prefix="/query", tags=["multi-model-query"])


# =============================================================================
# SCHEMAS
# =============================================================================

class SemanticQueryRequest(BaseModel):
    """Semantic query request"""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    top_k: int = Field(
        default=STAGE1_TOP_K, ge=1, le=100,
        description="Stage 1 recall depth (utterance rows). Default is the benchmarked k.",
    )
    dataset_id: Optional[str] = Field(None, description="Optional dataset UUID filter")
    template_id: Optional[str] = Field(None, description="Optional template UUID filter")
    intent: Optional[str] = Field(
        None, description="Accepted for backward compatibility; routing does not use it"
    )
    include_alternatives: bool = Field(default=False, description="Include alternative APIs")
    include_slot_extraction: bool = Field(default=True, description="Whether to extract values from query")


class FinalOutput(BaseModel):
    """The resolved API call."""
    t_id: str
    api_name: str
    endpoint: str
    method: str
    confidence_score: float
    base_url: Optional[str] = None
    extracted_base_url: Optional[str] = None
    effective_base_url: Optional[str] = None
    url_source: Optional[str] = None
    request_schema: Optional[dict] = None
    response_schema: Optional[dict] = None
    extracted_request_body: Optional[dict] = None


class ExtractionInfo(BaseModel):
    """Stage 3 outcome. `ok=False` with `degraded=False` means validation failed."""
    ok: bool
    values: dict = {}
    missing_required: List[str] = []
    degraded: bool = False
    reason: Optional[str] = None
    attempts: int = 0
    latency_ms: float = 0.0
    model: Optional[str] = None


class RankingInfo(BaseModel):
    """Stage 2 outcome."""
    strategy: str
    degraded: bool = False
    degraded_reason: Optional[str] = None
    reranker_model: Optional[str] = None
    rows_cross_encoded: int = 0


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
    
    # Stage 3
    extracted_request_body: Optional[dict] = None
    extraction: Optional[ExtractionInfo] = None

    # Stage 2 + overall health of this answer
    ranking: Optional[RankingInfo] = None
    degraded: bool = False
    alternatives: Optional[List[dict]] = None

    # Flat fields kept for existing clients
    api_name: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    base_url: Optional[str] = None
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
@limiter.limit("60/minute")
async def semantic_search(
    request: Request,
    body: SemanticQueryRequest,
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
    dataset_id = uuid.UUID(body.dataset_id) if body.dataset_id else None
    template_id = uuid.UUID(body.template_id) if body.template_id else None

    result = await service.semantic_search(
        db=db,
        user_id=current_user.u_id,
        user_query=body.query,
        top_k=body.top_k,
        dataset_id=dataset_id,
        template_id=template_id,
        include_alternatives=body.include_alternatives,
        include_slot_extraction=body.include_slot_extraction,
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
    """Routing readiness for the caller: embedder reachable + indexed vectors."""
    from app.core.runtime import get_embedder
    from app.core.tenancy import tenant_session
    from app.services.pgvector_store import get_pgvector_store

    embedder = get_embedder()
    embedder_ok = await embedder.health()
    async with tenant_session(current_user.u_id) as tdb:
        stats = await get_pgvector_store().stats(tdb)
    return {
        "status": "ok" if embedder_ok and stats["total_rows"] else "not_ready",
        "embedder": {"model": embedder.model_id, "dimension": embedder.dimension,
                     "reachable": embedder_ok},
        "vectors": stats,
    }
