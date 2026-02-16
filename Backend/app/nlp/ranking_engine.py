# app/nlp/ranking_engine.py

"""
AI Ranking Engine - Two-Stage Retrieval Pipeline

DEPRECATION WARNING:
This module uses LEGACY hardcoded index names (embeddings_768).
For new development, use multi_model_semantic_service.py which:
- Uses model-specific Redis indexes (idx_vectors_{model_id})
- Enforces model governance
- Returns MODEL_MISMATCH errors for dimension mismatches

This legacy module is retained for backward compatibility only.
Migrate to multi_model_semantic_service.py for proper multi-model support.

Stage 1: Vector retrieval (Top-K=5) from Redis Vector DB
Stage 2: FlashRank reranking with ms-marco-MiniLM-L-12-v2
"""

import warnings
import os
import numpy as np
import json
from typing import List, Dict, Any
from redis.commands.search.query import Query
from app.redis_config import get_redis_client
from app.nlp.embedding_model import get_model
from app.core.logger import logger

# Issue deprecation warning at import time
warnings.warn(
    "ranking_engine.py is deprecated. Use multi_model_semantic_service.py for model-safe searches.",
    DeprecationWarning,
    stacklevel=2
)

# --- Configuration (Legacy) ---
# Dimension-based indexes for different embedding models.
# WARNING: This bypasses model governance and should NOT be used for new development.
INDEX_MAPPING = {
    384: "embeddings_384",
    768: "embeddings_768",
    1024: "embeddings_1024"
}
# LEGACY: Hardcoded fallback - bypasses multi-model system
DEFAULT_INDEX = "embeddings_768"  # DEPRECATED: Use model-specific index
DEFAULT_TOP_K = 5
RERANKER_MODEL = "ms-marco-MiniLM-L-12-v2"

def escape_redis_tag(value: str) -> str:
    """Escape special characters in Redis TAG field values (like hyphens in UUIDs)"""
    if value is None:
        return value
    return str(value).replace('-', '\\-')

# --- Lazy Loaded Components ---
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


FLASHRANK_CACHE_DIR = os.getenv("FLASHRANK_CACHE_DIR", "/app/storage/flashrank_cache")
def _get_reranker():
    """Lazy load FlashRank reranker for Stage 2"""
    global _reranker
    if _reranker is None:
        try:
            from flashrank import Ranker
            logger.info(f"Initializing FlashRank reranker: {RERANKER_MODEL}...")
            _reranker = Ranker(model_name=RERANKER_MODEL, cache_dir=FLASHRANK_CACHE_DIR)
            logger.info(f"FlashRank reranker ready: {RERANKER_MODEL}")
        except ImportError as e:
            logger.error("FlashRank not installed. Install with: pip install flashrank")
            raise ImportError("FlashRank is required for reranking. Install with: pip install flashrank") from e
        except Exception as e:
            logger.error(f"Failed to initialize FlashRank: {e}")
            raise
    return _reranker


def _get_redis(dimension: int = None):
    """Lazy load Redis connection and get index for specified dimension"""
    global _redis_client
    if _redis_client is None:
        logger.info("Connecting to Redis for ranking engine...")
        _redis_client = get_redis_client()
    
    # Determine index name based on dimension
    if dimension and dimension in INDEX_MAPPING:
        index_name = INDEX_MAPPING[dimension]
    else:
        index_name = DEFAULT_INDEX
    
    return _redis_client, _redis_client.ft(index_name), index_name


# --- Stage 1: Vector Retrieval ---
def stage1_vector_retrieval(
    user_query: str, 
    top_k: int = DEFAULT_TOP_K,
    user_id: str = None
) -> List[Dict[str, Any]]:
    """
    Stage 1: Vector Retrieval from Redis Vector DB (Multi-Tenant Secure)
    
    Performs top-K nearest-neighbor vector search using embeddings stored in Redis.
    
    Security: Filters by user_id to ensure tenant isolation.
    User A can ONLY search User A's embeddings.
    
    Rules:
    - Uses the embedding model associated with the dataset
    - Retrieves top-K most semantically relevant documents
    - Does NOT modify or hallucinate content
    - Returns results exactly as stored, preserving text integrity
    - Passes all K retrieved items to Stage 2, no filtering
    
    Args:
        user_query: The search query from the user
        top_k: Number of candidates to retrieve (default: 5)
        user_id: User ID for multi-tenant isolation (REQUIRED for security)
    
    Returns:
        List of top-K candidate documents with their vector similarity scores
    """
    logger.info(f"[Stage 1] Vector retrieval for: '{user_query}' (top_k={top_k}, user_id={user_id})")
    
    # Get embedding model and Redis connection
    model = _get_embedding_model()
    embed_dim = model.get_sentence_embedding_dimension()
    _, ft, index_name = _get_redis(embed_dim)
    
    logger.info(f"[Stage 1] Using index: {index_name} (dimension={embed_dim})")
    
    # Encode query to vector
    query_vec = model.encode([user_query], normalize_embeddings=True)
    query_vec_bytes = np.asarray(query_vec, dtype=np.float32).tobytes()
    
    # Build KNN query with user_id filter for multi-tenant security
    # If user_id is provided, filter by user_id TAG field
    # Otherwise, search all (for backward compatibility, but should require user_id in production)
    if user_id:
        # SECURE: Filter by user_id - only return this user's embeddings
        escaped_user_id = escape_redis_tag(str(user_id))
        filter_query = f"(@user_id:{{{escaped_user_id}}})"
        knn_query = f"{filter_query}=>[KNN $k @vector $vec AS vector_score]"
    else:
        # WARNING: No user filter - searches ALL tenants (legacy mode)
        logger.warning("[Stage 1] No user_id provided - searching ALL embeddings (insecure)")
        knn_query = "*=>[KNN $k @vector $vec AS vector_score]"
    
    q = (
        Query(knn_query)
        .sort_by("vector_score")
        .return_fields("query", "api", "endpoint", "method", "scenario_type", "test_category", "notes", "user_id", "t_id", "vector_score")
        .dialect(2)
    )
    
    params = {"vec": query_vec_bytes, "k": top_k}
    results = ft.search(q, query_params=params)
    
    # Parse results - preserve original text integrity
    candidates = []
    for rank, doc in enumerate(results.docs, start=1):
        try:
            vector_distance = _safe_float(doc.vector_score, 1.0)
            vector_similarity = _safe_float(1.0 - vector_distance, 0.0)  # Convert distance to similarity
            
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
                "method": getattr(doc, "method", "POST"),  # Default to POST if not specified
                "scenario_type": getattr(doc, "scenario_type", "valid"),
                "test_category": getattr(doc, "test_category", "valid_flow"),
                "notes": getattr(doc, "notes", ""),
                "t_id": getattr(doc, "t_id", ""),  # Template ID for PostgreSQL resolution
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
                "method": getattr(doc, "method", "POST"),
                "scenario_type": getattr(doc, "scenario_type", "valid"),
                "test_category": getattr(doc, "test_category", "valid_flow"),
                "notes": getattr(doc, "notes", ""),
                "t_id": getattr(doc, "t_id", ""),
            }
        candidates.append(candidate)
    
    logger.info(f"[Stage 1] Retrieved {len(candidates)} candidates from vector search")
    return candidates



# --- Stage 2: FlashRank Reranking ---
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
        # ENHANCED: Include API metadata in reranking text for better accuracy
        # FlashRank expects a list of dicts with 'id' and 'text' keys
        passages = []
        for i, candidate in enumerate(candidates):
            query_text = candidate.get("text", "").strip()
            if query_text:  # Only include non-empty texts
                # Build enhanced text with API metadata for better reranking
                api_name = candidate.get("api", "")
                endpoint = candidate.get("endpoint", "")
                method = candidate.get("method", "POST")
                
                # Enhanced text format: "{query} | API: {api_name} | {method} {endpoint}"
                # This helps FlashRank distinguish between similar queries across different APIs
                enhanced_text = query_text
                if api_name:
                    enhanced_text = f"{query_text} | API: {api_name} | {method} {endpoint}"
                
                passages.append({
                    "id": i,
                    "text": enhanced_text,  # Enhanced text for reranking
                    "original_text": query_text,  # Preserve original for display
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
            # Use original_text for display (not the enhanced text used for reranking)
            display_text = result.get("original_text", original_candidate.get("text", "")).strip()
            
            final_result = {
                "rank": new_rank,
                "score": _safe_float(result.get("score", 0.0)),  # FlashRank score (sanitized)
                "text": display_text,  # Original text for display
                "query": original_candidate.get("query", ""),
                "api": original_candidate.get("api", ""),
                "endpoint": original_candidate.get("endpoint", ""),
                "method": original_candidate.get("method", "POST"),
                "scenario_type": original_candidate.get("scenario_type", "valid"),
                "test_category": original_candidate.get("test_category", "valid_flow"),
                "notes": original_candidate.get("notes", ""),
                "vector_score": _safe_float(original_candidate.get("vector_score", 0.0)),
                "t_id": original_candidate.get("t_id", ""),  # Template ID for PostgreSQL resolution
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
            "method": c.get("method", "POST"),
            "scenario_type": c.get("scenario_type", "valid"),
            "test_category": c.get("test_category", "valid_flow"),
            "notes": c.get("notes", ""),
            "vector_score": c.get("vector_score", 0.0),
            "t_id": c.get("t_id", ""),
        } for i, c in enumerate(candidates)]
    except Exception as e:
        logger.error(f"[Stage 2] Reranking failed: {e}")
        raise


# --- Main Ranking Function ---
def rank_query(
    user_query: str, 
    top_k: int = DEFAULT_TOP_K,
    include_stage1_results: bool = False,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Two-Stage AI Ranking Engine (Multi-Tenant Secure)
    
    Stage 1: Vector Retrieval (Top-K=5) from Redis Vector DB
    Stage 2: FlashRank Reranking with ms-marco-MiniLM-L-12-v2
    
    Security: Requires user_id for tenant isolation.
    
    This function ensures:
    - Correct 2-stage retrieval pipeline (semantic -> rerank)
    - Uses Redis Vector DB Top-K candidates
    - FlashRank with ms-marco-MiniLM-L-12-v2 for high-accuracy reranking
    - Zero hallucination, fully deterministic behavior
    - Multi-tenant isolation via user_id filtering
    
    Args:
        user_query: The search query from the user
        top_k: Number of candidates to retrieve in Stage 1 (default: 5)
        include_stage1_results: Whether to include Stage 1 results in output
        user_id: User ID for multi-tenant isolation (REQUIRED for security)
    
    Returns:
        JSON-ready dictionary with query and ranked_results
    """
    logger.info(f"[Ranking Engine] Starting two-stage retrieval for: '{user_query}' (user_id={user_id})")
    
    # Stage 1: Vector Retrieval (with user_id filter for security)
    stage1_candidates = stage1_vector_retrieval(user_query, top_k=top_k, user_id=user_id)
    
    # Stage 2: FlashRank Reranking
    reranked_results = stage2_flashrank_rerank(user_query, stage1_candidates)
    
    # Build final output with complete JSON for best result
    output = {
        "query": user_query,
        "best_result": reranked_results[0] if reranked_results else None,  # Complete JSON of best match
        "ranked_results": [
            {
                "rank": result["rank"],
                "score": result["score"],
                "text": result["text"],
                "api": result.get("api", ""),
                "endpoint": result.get("endpoint", ""),
                "method": result.get("method", ""),
                "scenario_type": result.get("scenario_type", ""),
                "test_category": result.get("test_category", ""),
                "notes": result.get("notes", ""),
                "vector_score": result.get("vector_score", 0.0)
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
    top_k: int = DEFAULT_TOP_K,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Detailed two-stage ranking with full metadata (Multi-Tenant Secure)
    
    Returns both Stage 1 and Stage 2 results with all metadata.
    
    Security: Requires user_id for tenant isolation.
    
    Args:
        user_query: The search query from the user
        top_k: Number of candidates to retrieve in Stage 1 (default: 5)
        user_id: User ID for multi-tenant isolation (REQUIRED for security)
    
    Returns:
        Dictionary with query, stage1_results, and ranked_results
    """
    logger.info(f"[Ranking Engine Detailed] Starting for: '{user_query}' (user_id={user_id})")
    
    # Stage 1: Vector Retrieval (with user_id filter for security)
    stage1_candidates = stage1_vector_retrieval(user_query, top_k=top_k, user_id=user_id)
    
    # Stage 2: FlashRank Reranking
    reranked_results = stage2_flashrank_rerank(user_query, stage1_candidates)
    
    return {
        "query": user_query,
        "stage1_results": [
            {
                "rank": c["rank"],
                "vector_score": _safe_float(c["vector_score"]),
                "text": c["text"],
                "api": c["api"],
                "endpoint": c["endpoint"],
                "method": c.get("method", "POST")
            }
            for c in stage1_candidates
        ],
        "ranked_results": reranked_results,
        "reranker_model": RERANKER_MODEL,
        "top_k": top_k
    }


# --- Utility Functions ---
def _safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to a JSON-compliant float.
    
    Handles NaN, Inf, -Inf, and invalid values by returning the default.
    This prevents JSON serialization errors.
    """
    import math
    try:
        f = float(value)
        # Check for NaN and Infinity which are not JSON compliant
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (TypeError, ValueError):
        return default


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