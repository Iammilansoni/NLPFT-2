# app/api/v1/ranking.py

"""
AI Ranking Engine API - Two-Stage Retrieval Pipeline (MULTI-TENANT SECURE)

Stage 1: Vector retrieval (Top-K=5) from Redis Vector DB
Stage 2: FlashRank reranking with ms-marco-MiniLM-L-12-v2

SECURITY: All endpoints require authentication and filter by user_id
This API provides high-precision semantic search with cross-encoder reranking.
"""

from fastapi import APIRouter, Query, HTTPException, Body, Depends
from typing import Optional, Union, Annotated
from app.nlp.ranking_engine import (
    rank_query, 
    rank_query_detailed, 
    get_reranker_info,
    stage1_vector_retrieval,
    stage2_flashrank_rerank,
)
from app.models.schemas import (
    RankingRequest,
    RankingResponse,
    DetailedRankingResponse,
    RerankerInfoResponse,
)
from app.api.v1.auth import get_current_user
from app.models.database_models import User
from app.core.logger import logger

router = APIRouter()


@router.post("/rank", response_model=RankingResponse)
async def rank_documents(
    request: RankingRequest = Body(..., description="Ranking request with query and options"),
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """
    Two-Stage AI Ranking Engine (MULTI-TENANT SECURE)
    
    AUTHENTICATION REQUIRED - Returns only the current user's embeddings
    
    Performs a two-stage retrieval pipeline:
    
    **Stage 1 - Vector Retrieval (Top-K):**
    - Uses embeddings stored in Redis Vector DB
    - Filters by user_id for multi-tenant isolation
    - Performs top-K nearest-neighbor vector search
    - Retrieves top-K most semantically relevant documents
    - Returns results exactly as stored, preserving text integrity
    
    **Stage 2 - FlashRank Reranking (ms-marco-MiniLM-L-12-v2):**
    - Applies high-precision cross-encoder reranking
    - Pairs each candidate with the user query
    - Computes accurate relevance scores
    - Reorders candidates strictly by reranker score (highest → lowest)
    
    **Important Rules:**
    - No hallucination: cannot create text that wasn't retrieved
    - No altering dataset text except minor whitespace trimming
    - Always trust cross-encoder scores over vector similarity
    - Maintain deterministic, stable ranking behavior
    - Multi-tenant isolation: only returns current user's data
    
    **Response Format:**
    ```json
    {
      "query": "<USER_QUERY>",
      "ranked_results": [
        {"rank": 1, "score": <flashrank_score>, "text": "<candidate_text>"},
        ...
      ]
    }
    ```
    """
    try:
        user_id = str(current_user.u_id) if current_user else None
        logger.info(f"[Ranking API] Request: query='{request.query}', top_k={request.top_k}, user_id={user_id}")
        
        result = rank_query(
            user_query=request.query,
            top_k=request.top_k,
            include_stage1_results=False,
            user_id=user_id
        )
        
        return RankingResponse(**result)
        
    except ImportError as e:
        logger.error(f"[Ranking API] FlashRank not installed: {e}")
        raise HTTPException(
            status_code=503,
            detail="FlashRank reranker not available. Please install: pip install flashrank"
        )
    except Exception as e:
        logger.error(f"[Ranking API] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rank/detailed", response_model=DetailedRankingResponse)
async def rank_documents_detailed(
    request: RankingRequest = Body(..., description="Ranking request with query and options"),
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """
    Detailed Two-Stage AI Ranking Engine (MULTI-TENANT SECURE)
    
    AUTHENTICATION REQUIRED - Returns only the current user's embeddings
    
    Same as `/rank` but returns complete details including:
    - Stage 1 vector retrieval results with similarity scores
    - Stage 2 reranked results with full metadata
    - API names, endpoints, request/response payloads
    - Original vector scores alongside FlashRank scores
    
    Use this endpoint for debugging, analysis, or when you need full metadata.
    """
    try:
        user_id = str(current_user.u_id) if current_user else None
        logger.info(f"[Ranking API Detailed] Request: query='{request.query}', top_k={request.top_k}, user_id={user_id}")
        
        result = rank_query_detailed(
            user_query=request.query,
            top_k=request.top_k,
            user_id=user_id
        )
        
        return DetailedRankingResponse(**result)
        
    except ImportError as e:
        logger.error(f"[Ranking API Detailed] FlashRank not installed: {e}")
        raise HTTPException(
            status_code=503,
            detail="FlashRank reranker not available. Please install: pip install flashrank"
        )
    except Exception as e:
        logger.error(f"[Ranking API Detailed] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rank", response_model=RankingResponse)
async def rank_documents_get(
    query: str = Query(..., min_length=1, description="Search query text"),
    top_k: Optional[int] = Query(5, ge=1, le=50, description="Number of candidates to retrieve (default: 5)"),
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """
    Two-Stage AI Ranking Engine (GET) (MULTI-TENANT SECURE)
    
    AUTHENTICATION REQUIRED - Returns only the current user's embeddings
    
    GET version of the ranking endpoint for simple queries.
    
    Same two-stage pipeline:
    1. Vector retrieval from Redis (Top-K) - filtered by user_id
    2. FlashRank reranking with ms-marco-MiniLM-L-12-v2
    """
    try:
        user_id = str(current_user.u_id) if current_user else None
        logger.info(f"[Ranking API GET] Request: query='{query}', top_k={top_k}, user_id={user_id}")
        
        result = rank_query(
            user_query=query,
            top_k=top_k,
            include_stage1_results=False,
            user_id=user_id
        )
        
        return RankingResponse(**result)
        
    except ImportError as e:
        logger.error(f"[Ranking API GET] FlashRank not installed: {e}")
        raise HTTPException(
            status_code=503,
            detail="FlashRank reranker not available. Please install: pip install flashrank"
        )
    except Exception as e:
        logger.error(f"[Ranking API GET] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rank/info", response_model=RerankerInfoResponse)
async def get_ranking_info():
    """
    Get Reranker Model Information
    
    Returns information about the cross-encoder model used for reranking:
    - Model name: ms-marco-MiniLM-L-12-v2
    - Type: Cross-encoder
    - Framework: FlashRank
    """
    try:
        info = get_reranker_info()
        return RerankerInfoResponse(**info)
    except Exception as e:
        logger.error(f"[Ranking Info] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rank/stage1")
async def rank_stage1_only(
    request: RankingRequest = Body(..., description="Ranking request"),
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """
    Stage 1 Only - Vector Retrieval (MULTI-TENANT SECURE)
    
    AUTHENTICATION REQUIRED - Returns only the current user's embeddings
    
    Performs only Stage 1 of the pipeline:
    - Vector search in Redis Vector DB
    - Returns top-K candidates by vector similarity
    - No reranking applied
    
    Useful for debugging or when you only need semantic search without reranking.
    """
    try:
        user_id = str(current_user.u_id) if current_user else None
        logger.info(f"[Stage 1 Only] Request: query='{request.query}', top_k={request.top_k}, user_id={user_id}")
        
        candidates = stage1_vector_retrieval(
            user_query=request.query,
            top_k=request.top_k,
            user_id=user_id
        )
        
        return {
            "query": request.query,
            "stage": "stage1_vector_retrieval",
            "top_k": request.top_k,
            "candidates": candidates
        }
        
    except Exception as e:
        logger.error(f"[Stage 1 Only] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rank/stage2")
async def rank_stage2_only(
    query: str = Body(..., embed=True, description="User query for reranking"),
    candidates: list = Body(..., embed=True, description="Candidates from Stage 1 to rerank"),
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """
    Stage 2 Only - FlashRank Reranking (MULTI-TENANT SECURE)
    
    AUTHENTICATION REQUIRED
    
    Performs only Stage 2 of the pipeline:
    - Takes pre-retrieved candidates as input
    - Applies FlashRank cross-encoder reranking
    - Returns reranked results by relevance score
    
    Useful for custom pipelines or when candidates come from a different source.
    
    **Request Body:**
    ```json
    {
      "query": "your search query",
      "candidates": [
        {"text": "candidate 1 text", ...},
        {"text": "candidate 2 text", ...}
      ]
    }
    ```
    """
    try:
        user_id = str(current_user.u_id) if current_user else None
        logger.info(f"[Stage 2 Only] Request: query='{query}', {len(candidates)} candidates, user_id={user_id}")
        
        # Ensure candidates have required 'text' field
        validated_candidates = []
        for i, c in enumerate(candidates):
            if isinstance(c, dict):
                validated_candidates.append({
                    "text": c.get("text", ""),
                    "rank": c.get("rank", i + 1),
                    "vector_score": c.get("vector_score", 0.0),
                    **{k: v for k, v in c.items() if k not in ["text", "rank", "vector_score"]}
                })
            elif isinstance(c, str):
                validated_candidates.append({
                    "text": c,
                    "rank": i + 1,
                    "vector_score": 0.0
                })
        
        reranked = stage2_flashrank_rerank(
            user_query=query,
            candidates=validated_candidates
        )
        
        return {
            "query": query,
            "stage": "stage2_flashrank_rerank",
            "reranker_model": "ms-marco-MiniLM-L-12-v2",
            "ranked_results": reranked
        }
        
    except ImportError as e:
        logger.error(f"[Stage 2 Only] FlashRank not installed: {e}")
        raise HTTPException(
            status_code=503,
            detail="FlashRank reranker not available. Please install: pip install flashrank"
        )
    except Exception as e:
        logger.error(f"[Stage 2 Only] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Semantic API Retrieval Pipeline ---

from app.models.schemas import (
    SemanticRetrievalRequest,
    SemanticRetrievalResponse,
)
# Migrated to multi-model semantic service for proper model governance
from app.services.multi_model_semantic_service import get_multi_model_semantic_service
from app.core.postgres import get_db


@router.post("/semantic-retrieve", response_model=SemanticRetrievalResponse)
async def semantic_retrieve_api(
    request: SemanticRetrievalRequest = Body(..., description="Semantic retrieval request"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db = Depends(get_db)
):
    """
    Semantic API Retrieval Pipeline (MULTI-TENANT SECURE)
    
    AUTHENTICATION REQUIRED - Resolves APIs from PostgreSQL templates
    
    **Complete 5-Stage Pipeline with Model Governance:**
    
    1. **Get Active Model from Settings** - Source of truth for embedding model
       - Reads user's default_embedding_model from UserSettings
       - Validates model is compatible with dataset
    
    2. **Vector Search (Redis)** - Model-specific index
       - Uses idx_vectors_{model_id} instead of shared index
       - Ensures dimension-safe searches
    
    3. **Group by t_id** - Aggregation
       - Groups results by template ID
       - Each group represents one candidate API
    
    4. **Re-rank Candidates** - Decision stage
       - Model-agnostic scoring (uses similarity/confidence)
       - Selects best template
    
    5. **Resolve from PostgreSQL** - Authority stage
       - Fetches full API template from database
       - PostgreSQL is the SINGLE SOURCE OF TRUTH
    
    **Model Governance:**
    - Returns MODEL_MISMATCH error if user's model != dataset's model
    - Query embedding uses same model as dataset
    - No silent searches against wrong index
    """
    import time
    start_time = time.time()
    
    try:
        user_id = current_user.u_id
        logger.info(f"[Semantic Retrieval API] Request: query='{request.query[:50]}...', "
                   f"top_k={request.top_k}, user_id={str(user_id)[:8]}...")
        
        # Use the new multi-model semantic service
        semantic_service = get_multi_model_semantic_service()
        result = await semantic_service.semantic_search(
            db=db,
            user_id=user_id,
            user_query=request.query,
            top_k=request.top_k,
            user_query_intent=request.intent_type,
            include_alternatives=request.include_alternatives,
            include_slot_extraction=request.include_slot_extraction
        )
        
        # Handle MODEL_MISMATCH error gracefully
        if not result.get("success", False) and result.get("error") == "MODEL_MISMATCH":
            logger.warning(f"[Semantic Retrieval API] Model mismatch for user {str(user_id)[:8]}")
            # Return the mismatch response with proper HTTP status
            raise HTTPException(
                status_code=409,  # Conflict
                detail=result
            )
        
        # Record performance metric
        total_latency = (time.time() - start_time) * 1000  # ms
        processing_time = result.get("metadata", {}).get("processing_time_ms", total_latency)
        
        try:
            from app.api.v1.telemetry import record_metric, PerformanceMetric
            from datetime import datetime, timezone
            
            metric = PerformanceMetric(
                timestamp=datetime.now(timezone.utc).isoformat(),
                search_latency_ms=processing_time * 0.4,  # Estimate 40% for search
                embedding_latency_ms=processing_time * 0.2,  # Estimate 20% for embedding
                reranker_latency_ms=processing_time * 0.3,  # Estimate 30% for reranking
                total_latency_ms=total_latency,
                result_count=len(result.get("stage1_vector_search", [])),
                user_id=str(user_id)
            )
            record_metric(metric)
        except Exception as e:
            logger.debug(f"Failed to record telemetry: {e}")
        
        return SemanticRetrievalResponse(**result)
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"[Semantic Retrieval API] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semantic-retrieve", response_model=SemanticRetrievalResponse)
async def semantic_retrieve_api_get(
    query: str = Query(..., min_length=1, description="Natural language query"),
    top_k: int = Query(5, ge=1, le=50, description="Number of candidates to retrieve"),
    intent_type: Optional[str] = Query(None, description="Query intent hint"),
    include_alternatives: bool = Query(False, description="Include alternative suggestions"),
    include_slot_extraction: bool = Query(True, description="Extract values from query to populate request schema"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db = Depends(get_db)
):
    """
    Semantic API Retrieval Pipeline (GET) (MULTI-TENANT SECURE)
    
    AUTHENTICATION REQUIRED
    
    GET version of the semantic retrieval endpoint with model governance.
    Uses multi_model_semantic_service for proper dimension-safe searches.
    
    **Model Governance:**
    - Returns MODEL_MISMATCH error (HTTP 409) if model mismatch
    - Uses user's Settings model for query embedding
    - Searches model-specific Redis index
    """
    try:
        user_id = current_user.u_id
        logger.info(f"[Semantic Retrieval API GET] Request: query='{query[:50]}...', "
                   f"top_k={top_k}, user_id={str(user_id)[:8]}...")
        
        # Use the new multi-model semantic service
        semantic_service = get_multi_model_semantic_service()
        result = await semantic_service.semantic_search(
            db=db,
            user_id=user_id,
            user_query=query,
            top_k=top_k,
            user_query_intent=intent_type,
            include_alternatives=include_alternatives,
            include_slot_extraction=include_slot_extraction
        )
        
        # Handle MODEL_MISMATCH error gracefully
        if not result.get("success", False) and result.get("error") == "MODEL_MISMATCH":
            logger.warning(f"[Semantic Retrieval API GET] Model mismatch for user {str(user_id)[:8]}")
            raise HTTPException(
                status_code=409,  # Conflict
                detail=result
            )
        
        return SemanticRetrievalResponse(**result)
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"[Semantic Retrieval API GET] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
