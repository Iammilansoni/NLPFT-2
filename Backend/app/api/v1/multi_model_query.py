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
from app.core.postgres import get_db
from app.core.rate_limit import limiter
from app.models.schemas import UserResponse
from app.nlp.cross_encoder_reranker import STAGE1_TOP_K
from app.services.multi_model_embedding_service import (
    get_multi_model_embedding_service,
    queue_embedding,
)
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

    # Model governance: how to make datasets from other embedding models searchable
    options: Optional[List[dict]] = None

    # Flat fields kept for existing clients
    api_name: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    base_url: Optional[str] = None
    confidence: Optional[float] = None


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
    Route a natural-language request to one API template.

    Searches with the caller's embedding model (Settings -> Embedding model).
    Datasets embedded with another model are never compared against it: they
    come back in `metadata.excluded_datasets`, with `options` to switch model
    or re-embed.

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
    force_reembed: bool = Query(False, description="Replace vectors made with another model"),
):
    """Embed a dataset with the caller's embedding model, on the worker."""
    return await queue_embedding(db, current_user.u_id, dataset_id, force_reembed=force_reembed)


@router.post("/datasets/{dataset_id}/reembed")
async def reembed_dataset(
    dataset_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Replace a dataset's vectors using the caller's embedding model."""
    return await queue_embedding(db, current_user.u_id, dataset_id, force_reembed=True)


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


@router.get("/health")
async def query_service_health(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Routing readiness for the caller: their embedding model reachable + vectors indexed for it."""
    from app.core.tenancy import tenant_session
    from app.llm.embeddings import EmbeddingError
    from app.services.model_access import active_embedding, embedder_for
    from app.services.pgvector_store import get_pgvector_store

    active = await active_embedding(db, current_user.u_id)
    try:
        embedder_ok = await (await embedder_for(db, current_user.u_id, active)).health()
        problem = None if embedder_ok else f"{active.label} is not reachable."
    except EmbeddingError as exc:
        embedder_ok, problem = False, exc.message
    async with tenant_session(current_user.u_id) as tdb:
        stats = await get_pgvector_store().stats(tdb)
    indexed = sum(
        m["rows"] for m in stats["by_model"]
        if active.matches(m["provider"], m["model"], m["dimension"])
    )
    return {
        "status": "ok" if embedder_ok and indexed else "not_ready",
        "embedding": {**active.to_dict(), "reachable": embedder_ok, "problem": problem},
        "indexed_rows_for_active_model": indexed,
        "vectors": stats,
    }
