# app/nlp/ranking_engine.py

"""
AI Ranking Engine - Two-Stage Retrieval Pipeline
Stage 1: Vector retrieval (Top-K=5) from Redis Vector DB
Stage 2: FlashRank reranking with ms-marco-MiniLM-L-12-v2

This module provides a high-precision semantic search with cross-encoder reranking.
"""

import numpy as np
import json
from typing import List, Dict, Any, Optional
from redis.commands.search.query import Query
from app.redis_config import get_redis_client
from app.nlp.embedding_model import get_model
from app.core.logger import logger

# ===============================================================
# CONFIGURATION
# ===============================================================
INDEX_NAME = "idx:api"
DEFAULT_TOP_K = 5
RERANKER_MODEL = "ms-marco-MiniLM-L-12-v2"

# ===============================================================
# LAZY LOADED COMPONENTS
# ===============================================================
_embedding_model = None
_embed_dim = None
_reranker = None
_redis_client = None
_ft = None


def _get_embedding_model():
    """Lazy load embedding model for Stage 1 vector search"""
    global _embedding_model, _embed_dim
    if _embedding_model is None:
        logger.info("Initializing embedding model for ranking engine...")
        _embedding_model = get_model()
        _embedding_model.max_seq_length = 256
        _embed_dim = _embedding_model.get_sentence_embedding_dimension()
        logger.info(f"Embedding model ready. Dimension: {_embed_dim}")
    return _embedding_model


def _get_reranker():
    """Lazy load FlashRank reranker for Stage 2"""
    global _reranker
    if _reranker is None:
        try:
            from flashrank import Ranker, RerankRequest
            logger.info(f"Initializing FlashRank reranker: {RERANKER_MODEL}...")
            _reranker = Ranker(model_name=RERANKER_MODEL, cache_dir="/tmp/flashrank_cache")
            logger.info(f"FlashRank reranker ready: {RERANKER_MODEL}")
        except ImportError as e:
            logger.error(f"FlashRank not installed. Install with: pip install flashrank")
            raise ImportError("FlashRank is required for reranking. Install with: pip install flashrank") from e
        except Exception as e:
            logger.error(f"Failed to initialize FlashRank: {e}")
            raise
    return _reranker


def _get_redis():
    """Lazy load Redis connection"""
    global _redis_client, _ft
    if _redis_client is None:
        logger.info("Connecting to Redis for ranking engine...")
        _redis_client = get_redis_client()
        _ft = _redis_client.ft(INDEX_NAME)
    return _redis_client, _ft


# ===============================================================
# STAGE 1: VECTOR RETRIEVAL (Top-K from Redis)
# ===============================================================
def stage1_vector_retrieval(user_query: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
    """
    Stage 1: Vector Retrieval from Redis Vector DB
    
    Performs top-K nearest-neighbor vector search using embeddings stored in Redis.
    
    Rules:
    - Uses the embedding model associated with the dataset
    - Retrieves top-K most semantically relevant documents
    - Does NOT modify or hallucinate content
    - Returns results exactly as stored, preserving text integrity
    - Passes all K retrieved items to Stage 2, no filtering
    
    Args:
        user_query: The search query from the user
        top_k: Number of candidates to retrieve (default: 5)
    
    Returns:
        List of top-K candidate documents with their vector similarity scores
    """
    logger.info(f"[Stage 1] Vector retrieval for: '{user_query}' (top_k={top_k})")
    
    # Get embedding model and Redis connection
    model = _get_embedding_model()
    _, ft = _get_redis()
    
    # Encode query to vector
    query_vec = model.encode([user_query], normalize_embeddings=True)
    query_vec_bytes = np.asarray(query_vec, dtype=np.float32).tobytes()
    
    # Build KNN query
    q = (
        Query("*=>[KNN $k @query_embedding $vec AS vector_score]")
        .sort_by("vector_score")
        .return_fields("query", "api", "endpoint", "request", "response", "vector_score")
        .dialect(2)
    )
    
    params = {"vec": query_vec_bytes, "k": top_k}
    results = ft.search(q, query_params=params)
    
    # Parse results - preserve original text integrity
    candidates = []
    for rank, doc in enumerate(results.docs, start=1):
        try:
            vector_distance = float(doc.vector_score)
            vector_similarity = 1.0 - vector_distance  # Convert distance to similarity
            
            # Extract the text content for reranking (using query field as the primary text)
            text_content = getattr(doc, "query", "")
            
            candidate = {
                "rank": rank,
                "vector_score": vector_similarity,
                "vector_distance": vector_distance,
                "text": text_content,  # Primary text for reranking
                "query": text_content,
                "api": getattr(doc, "api", ""),
                "endpoint": getattr(doc, "endpoint", ""),
                "request": _safe_json_parse(getattr(doc, "request", "{}")),
                "response": _safe_json_parse(getattr(doc, "response", "{}")),
            }
        except Exception as e:
            logger.warning(f"Error parsing document: {e}")
            candidate = {
                "rank": rank,
                "vector_score": 0.0,
                "vector_distance": 1.0,
                "text": getattr(doc, "query", ""),
                "query": getattr(doc, "query", ""),
                "api": getattr(doc, "api", ""),
                "endpoint": getattr(doc, "endpoint", ""),
                "request": {},
                "response": {},
            }
        candidates.append(candidate)
    
    logger.info(f"[Stage 1] Retrieved {len(candidates)} candidates from vector search")
    return candidates


# ===============================================================
# STAGE 2: FLASHRANK RERANKING
# ===============================================================
def stage2_flashrank_rerank(
    user_query: str, 
    candidates: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Stage 2: FlashRank Reranking with ms-marco-MiniLM-L-12-v2
    
    Applies high-precision reranking using FlashRank cross-encoder model.
    
    Process:
    1. Accept the top-K candidates from Stage 1
    2. Pair each candidate with the user query
    3. Use FlashRank with ms-marco-MiniLM-L-12-v2 to compute relevance scores
    4. Reorder candidates strictly by reranker's score (highest → lowest)
    
    Important Rules:
    - No hallucination: cannot create text that wasn't retrieved
    - No altering dataset text except minor whitespace trimming
    - If a candidate is low quality, still rank it honestly
    - Never generate new content — only rank existing candidates
    - Always trust cross-encoder scores over vector similarity
    - Maintain deterministic, stable ranking behavior
    
    Args:
        user_query: The original search query
        candidates: List of candidates from Stage 1 vector retrieval
    
    Returns:
        Reranked list of candidates ordered by FlashRank scores (highest first)
    """
    if not candidates:
        logger.warning("[Stage 2] No candidates to rerank")
        return []
    
    logger.info(f"[Stage 2] Reranking {len(candidates)} candidates with FlashRank ({RERANKER_MODEL})")
    
    try:
        from flashrank import RerankRequest
        reranker = _get_reranker()
        
        # Prepare passages for reranking
        # FlashRank expects a list of dicts with 'id' and 'text' keys
        passages = []
        for i, candidate in enumerate(candidates):
            text = candidate.get("text", "").strip()
            if text:  # Only include non-empty texts
                passages.append({
                    "id": i,
                    "text": text,
                    "meta": candidate  # Store original candidate data
                })
        
        if not passages:
            logger.warning("[Stage 2] No valid passages to rerank, returning original order")
            return candidates
        
        # Create rerank request
        rerank_request = RerankRequest(
            query=user_query,
            passages=passages
        )
        
        # Perform reranking
        reranked_results = reranker.rerank(rerank_request)
        
        # Build final results with FlashRank scores
        final_results = []
        for new_rank, result in enumerate(reranked_results, start=1):
            original_candidate = result.get("meta", candidates[result.get("id", 0)])
            
            final_result = {
                "rank": new_rank,
                "score": float(result.get("score", 0.0)),  # FlashRank score
                "text": result.get("text", "").strip(),
                "query": original_candidate.get("query", ""),
                "api": original_candidate.get("api", ""),
                "endpoint": original_candidate.get("endpoint", ""),
                "request": original_candidate.get("request", {}),
                "response": original_candidate.get("response", {}),
                "vector_score": original_candidate.get("vector_score", 0.0),
            }
            final_results.append(final_result)
        
        logger.info(f"[Stage 2] Reranking complete. Top result score: {final_results[0]['score'] if final_results else 'N/A'}")
        return final_results
        
    except ImportError:
        logger.error("[Stage 2] FlashRank not available, returning candidates with vector scores only")
        # Fallback: return original order with vector scores
        return [{
            "rank": i + 1,
            "score": c.get("vector_score", 0.0),
            "text": c.get("text", ""),
            "query": c.get("query", ""),
            "api": c.get("api", ""),
            "endpoint": c.get("endpoint", ""),
            "request": c.get("request", {}),
            "response": c.get("response", {}),
            "vector_score": c.get("vector_score", 0.0),
        } for i, c in enumerate(candidates)]
    except Exception as e:
        logger.error(f"[Stage 2] Reranking failed: {e}")
        raise


# ===============================================================
# MAIN RANKING FUNCTION
# ===============================================================
def rank_query(
    user_query: str, 
    top_k: int = DEFAULT_TOP_K,
    include_stage1_results: bool = False
) -> Dict[str, Any]:
    """
    Two-Stage AI Ranking Engine
    
    Stage 1: Vector Retrieval (Top-K=5) from Redis Vector DB
    Stage 2: FlashRank Reranking with ms-marco-MiniLM-L-12-v2
    
    This function ensures:
    ✅ Correct 2-stage retrieval pipeline (semantic → rerank)
    ✅ Uses Redis Vector DB Top-K candidates
    ✅ FlashRank with ms-marco-MiniLM-L-12-v2 for high-accuracy reranking
    ✅ Zero hallucination, fully deterministic behavior
    
    Args:
        user_query: The search query from the user
        top_k: Number of candidates to retrieve in Stage 1 (default: 5)
        include_stage1_results: Whether to include Stage 1 results in output
    
    Returns:
        JSON-ready dictionary with query and ranked_results
    """
    logger.info(f"[Ranking Engine] Starting two-stage retrieval for: '{user_query}'")
    
    # Stage 1: Vector Retrieval
    stage1_candidates = stage1_vector_retrieval(user_query, top_k=top_k)
    
    # Stage 2: FlashRank Reranking
    reranked_results = stage2_flashrank_rerank(user_query, stage1_candidates)
    
    # Build final output
    output = {
        "query": user_query,
        "ranked_results": [
            {
                "rank": result["rank"],
                "score": result["score"],
                "text": result["text"]
            }
            for result in reranked_results
        ]
    }
    
    # Optionally include detailed results
    if include_stage1_results:
        output["stage1_candidates"] = stage1_candidates
        output["detailed_results"] = reranked_results
    
    logger.info(f"[Ranking Engine] Complete. Returned {len(reranked_results)} ranked results")
    return output


def rank_query_detailed(
    user_query: str, 
    top_k: int = DEFAULT_TOP_K
) -> Dict[str, Any]:
    """
    Detailed two-stage ranking with full metadata.
    
    Returns both Stage 1 and Stage 2 results with all metadata.
    
    Args:
        user_query: The search query from the user
        top_k: Number of candidates to retrieve in Stage 1 (default: 5)
    
    Returns:
        Dictionary with query, stage1_results, and ranked_results
    """
    logger.info(f"[Ranking Engine Detailed] Starting for: '{user_query}'")
    
    # Stage 1: Vector Retrieval
    stage1_candidates = stage1_vector_retrieval(user_query, top_k=top_k)
    
    # Stage 2: FlashRank Reranking
    reranked_results = stage2_flashrank_rerank(user_query, stage1_candidates)
    
    return {
        "query": user_query,
        "stage1_results": [
            {
                "rank": c["rank"],
                "vector_score": c["vector_score"],
                "text": c["text"],
                "api": c["api"],
                "endpoint": c["endpoint"]
            }
            for c in stage1_candidates
        ],
        "ranked_results": reranked_results,
        "reranker_model": RERANKER_MODEL,
        "top_k": top_k
    }


# ===============================================================
# UTILITY FUNCTIONS
# ===============================================================
def _safe_json_parse(value: str) -> Dict[str, Any]:
    """Safely parse JSON string, returning empty dict on failure"""
    if not value:
        return {}
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError):
        return {}


def get_reranker_info() -> Dict[str, Any]:
    """Get information about the reranker model"""
    return {
        "model_name": RERANKER_MODEL,
        "type": "cross-encoder",
        "framework": "FlashRank",
        "description": "High-precision reranker using ms-marco-MiniLM-L-12-v2 cross-encoder"
    }
