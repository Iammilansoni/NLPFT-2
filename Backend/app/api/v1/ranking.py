# app/api/v1/ranking.py

"""
AI Ranking Engine API - Two-Stage Retrieval Pipeline

Stage 1: Vector retrieval (Top-K=5) from Redis Vector DB
Stage 2: FlashRank reranking with ms-marco-MiniLM-L-12-v2

This API provides high-precision semantic search with cross-encoder reranking.
"""

from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional, Union
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
from app.core.logger import logger

router = APIRouter()


@router.post("/rank", response_model=RankingResponse)
async def rank_documents(
    request: RankingRequest = Body(..., description="Ranking request with query and options")
):
    """
    🎯 Two-Stage AI Ranking Engine
    
    Performs a two-stage retrieval pipeline:
    
    **Stage 1 - Vector Retrieval (Top-K):**
    - Uses embeddings stored in Redis Vector DB
    - Performs top-K nearest-neighbor vector search
    - Retrieves top-K most semantically relevant documents
    - Returns results exactly as stored, preserving text integrity
    
    **Stage 2 - FlashRank Reranking (ms-marco-MiniLM-L-12-v2):**
    - Applies high-precision cross-encoder reranking
    - Pairs each candidate with the user query
    - Computes accurate relevance scores
    - Reorders candidates strictly by reranker score (highest → lowest)
    
    **Important Rules:**
    - ✅ No hallucination: cannot create text that wasn't retrieved
    - ✅ No altering dataset text except minor whitespace trimming
    - ✅ Always trust cross-encoder scores over vector similarity
    - ✅ Maintain deterministic, stable ranking behavior
    
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
        logger.info(f"[Ranking API] Request: query='{request.query}', top_k={request.top_k}")
        
        result = rank_query(
            user_query=request.query,
            top_k=request.top_k,
            include_stage1_results=False
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
    request: RankingRequest = Body(..., description="Ranking request with query and options")
):
    """
    🔍 Detailed Two-Stage AI Ranking Engine
    
    Same as `/rank` but returns complete details including:
    - Stage 1 vector retrieval results with similarity scores
    - Stage 2 reranked results with full metadata
    - API names, endpoints, request/response payloads
    - Original vector scores alongside FlashRank scores
    
    Use this endpoint for debugging, analysis, or when you need full metadata.
    """
    try:
        logger.info(f"[Ranking API Detailed] Request: query='{request.query}', top_k={request.top_k}")
        
        result = rank_query_detailed(
            user_query=request.query,
            top_k=request.top_k
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
    top_k: Optional[int] = Query(5, ge=1, le=50, description="Number of candidates to retrieve (default: 5)")
):
    """
    🎯 Two-Stage AI Ranking Engine (GET)
    
    GET version of the ranking endpoint for simple queries.
    
    Same two-stage pipeline:
    1. Vector retrieval from Redis (Top-K)
    2. FlashRank reranking with ms-marco-MiniLM-L-12-v2
    """
    try:
        logger.info(f"[Ranking API GET] Request: query='{query}', top_k={top_k}")
        
        result = rank_query(
            user_query=query,
            top_k=top_k,
            include_stage1_results=False
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
    ℹ️ Get Reranker Model Information
    
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
    request: RankingRequest = Body(..., description="Ranking request")
):
    """
    🔹 Stage 1 Only - Vector Retrieval
    
    Performs only Stage 1 of the pipeline:
    - Vector search in Redis Vector DB
    - Returns top-K candidates by vector similarity
    - No reranking applied
    
    Useful for debugging or when you only need semantic search without reranking.
    """
    try:
        logger.info(f"[Stage 1 Only] Request: query='{request.query}', top_k={request.top_k}")
        
        candidates = stage1_vector_retrieval(
            user_query=request.query,
            top_k=request.top_k
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
    candidates: list = Body(..., embed=True, description="Candidates from Stage 1 to rerank")
):
    """
    🔹 Stage 2 Only - FlashRank Reranking
    
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
        logger.info(f"[Stage 2 Only] Request: query='{query}', {len(candidates)} candidates")
        
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
