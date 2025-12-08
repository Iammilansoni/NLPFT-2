#app/nlp/semantic_search_service.py

"""
Semantic Search Service - Uses Ollama for embeddings (no HuggingFace)
"""

import numpy as np
import json
from redis.commands.search.query import Query
from app.redis_config import get_redis_client
from app.nlp.embedding_model import get_model
from app.core.logger import logger

# ===============================================================
# CONFIGURATION SECTION
# ===============================================================
INDEX_NAME = "idx:api"
TOP_K = 5

# ===============================================================
# MODEL INITIALIZATION (Lazy loaded)
# ===============================================================
# Uses Ollama HTTP API instead of HuggingFace SentenceTransformer
# Model is loaded on first use, not at module import
_model = None
_embed_dim = None

def _get_model():
    """Lazy load embedding model"""
    global _model, _embed_dim
    if _model is None:
        logger.info("Initializing Ollama embedding model...")
        _model = get_model()
        _model.max_seq_length = 256
        _embed_dim = _model.get_sentence_embedding_dimension()
        logger.info(f"Ollama model ready. Dimension: {_embed_dim}")
    return _model

def _get_embed_dim():
    """Get embedding dimension"""
    global _embed_dim
    if _embed_dim is None:
        _get_model()
    return _embed_dim

# For backward compatibility
model = property(lambda self: _get_model())
EMBED_DIM = property(lambda self: _get_embed_dim())

# ===============================================================
# REDIS CONNECTION (Lazy loaded)
# ===============================================================
_redis_client = None
_ft = None

def _get_redis():
    """Lazy load Redis connection"""
    global _redis_client, _ft
    if _redis_client is None:
        logger.info("Connecting to Redis...")
        _redis_client = get_redis_client()
        _ft = _redis_client.ft(INDEX_NAME)
    return _redis_client, _ft

# ===============================================================
# FUNCTION: semantic_search
# ===============================================================
# Purpose:
#   Performs semantic similarity search against the Redis vector database.
#
# Parameters:
#   user_query (str): The input query text entered by the user.
#   top_k (int): The number of top similar entries to retrieve.
#
# Process:
#   1. Encode the user query into a semantic vector using Ollama.
#   2. Perform a KNN search in Redis to find the closest embeddings.
#   3. Parse and return the matched documents in JSON format.
#
# Returns:
#   dict: A JSON-ready dictionary containing top search matches,
#         each with metadata like API name, endpoint, and similarity score.
# ===============================================================
def semantic_search(user_query: str, top_k: int = TOP_K):
    logger.info(f"Searching for: '{user_query}'")
    
    # Lazy load model and Redis connection
    model = _get_model()
    _, ft = _get_redis()

    query_vec = model.encode([user_query], normalize_embeddings=True)
    query_vec_bytes = np.asarray(query_vec, dtype=np.float32).tobytes()

    q = (
        Query("*=>[KNN $k @query_embedding $vec AS score]")
        .sort_by("score")
        .return_fields("query", "api", "endpoint", "request", "response", "score")
        .dialect(2)
    )

    params = {"vec": query_vec_bytes, "k": top_k}
    results = ft.search(q, query_params=params)

    matches = []
    for doc in results.docs:
        try:
            cosine_distance = float(doc.score)
            cosine_similarity = 1.0 - cosine_distance
            match_data = {
                "query": doc.query,
                "api": doc.api,
                "endpoint": doc.endpoint,
                "request": json.loads(doc.request) if doc.request else {},
                "response": json.loads(doc.response) if doc.response else {},
                "cosine_distance": cosine_distance,
                "cosine_similarity": cosine_similarity,
            }
        except Exception:
            match_data = {
                "query": getattr(doc, "query", ""),
                "api": getattr(doc, "api", ""),
                "endpoint": getattr(doc, "endpoint", ""),
                "request": getattr(doc, "request", ""),
                "response": getattr(doc, "response", ""),
                "cosine_distance": float(getattr(doc, "score", 1.0)),
                "cosine_similarity": 1.0 - float(getattr(doc, "score", 1.0)),
            }
        matches.append(match_data)

    return {
        "input_query": user_query,
        "top_k": top_k,
        "results": matches,
    }