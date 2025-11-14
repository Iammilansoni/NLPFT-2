#app/nlp/semantic_search_service.py

import numpy as np
import json
from sentence_transformers import SentenceTransformer
from redis.commands.search.query import Query
from app.redis_config import get_redis_client
from app.nlp.embedding_model import get_model

# ===============================================================
# CONFIGURATION SECTION
# ===============================================================
# Defines constants used across the module for model loading,
# Redis index name, and number of top search results to retrieve.
INDEX_NAME = "idx:api"
TOP_K = 5

# ===============================================================
# MODEL INITIALIZATION
# ===============================================================
# Loads a SentenceTransformer model for generating semantic embeddings
# and sets a max sequence length for text input. This model converts
# text queries and stored API descriptions into embedding vectors.
print("Loading embedding model...")
model = get_model()
model.max_seq_length = 256
EMBED_DIM = model.get_sentence_embedding_dimension()

# ===============================================================
# REDIS CONNECTION
# ===============================================================
# Creates a Redis client connection through a centralized configuration file.
# The index `idx:apis` is used to perform vector similarity (KNN) search
# against the pre-stored embeddings of API dataset entries.
print("Connecting to Redis...")
r = get_redis_client()
ft = r.ft(INDEX_NAME)

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
#   1. Encode the user query into a semantic vector.
#   2. Perform a KNN search in Redis to find the closest embeddings.
#   3. Parse and return the matched documents in JSON format.
#
# Returns:
#   dict: A JSON-ready dictionary containing top search matches,
#         each with metadata like API name, endpoint, and similarity score.
# ===============================================================
def semantic_search(user_query: str, top_k: int = TOP_K):
    print(f"\nSearching for: '{user_query}'")

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