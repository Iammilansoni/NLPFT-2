import numpy as np
import json
from sentence_transformers import SentenceTransformer
from redis.commands.search.query import Query
from redis_config import get_redis_client

# -------------------------------
# CONFIG
# -------------------------------
MODEL_NAME = "BAAI/bge-small-en-v1.5"
INDEX_NAME = "idx:apis"
TOP_K = 5

# -------------------------------
# LOAD MODEL
# -------------------------------
print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)
model.max_seq_length = 256
EMBED_DIM = model.get_sentence_embedding_dimension()

# -------------------------------
# CONNECT TO REDIS
# -------------------------------
print("Connecting to Redis...")
r = get_redis_client()
ft = r.ft(INDEX_NAME)

# -------------------------------
# SEMANTIC SEARCH FUNCTION
# -------------------------------
def semantic_search(user_query: str, top_k: int = TOP_K):
    print(f"\nSearching for: '{user_query}'")

    
    query_vec = model.encode([user_query], normalize_embeddings=True)
    query_vec = np.asarray(query_vec, dtype=np.float32).tobytes()

    
    q = (
        Query("*=>[KNN $k @query_embedding $vec AS score]")
        .sort_by("score")
        .return_fields("query", "api", "endpoint", "request", "response", "score")
        .dialect(2)
    )

    params = {"vec": query_vec, "k": top_k}
    results = ft.search(q, query_params=params)

   
    matches = []
    for doc in results.docs:
        try:
            match_data = {
                "query": doc.query,
                "api": doc.api,
                "endpoint": doc.endpoint,
                "request": json.loads(doc.request) if doc.request else {},
                "response": json.loads(doc.response) if doc.response else {},
                "score": float(doc.score),
            }
        except Exception:
            match_data = {
                "query": getattr(doc, "query", ""),
                "api": getattr(doc, "api", ""),
                "endpoint": getattr(doc, "endpoint", ""),
                "request": getattr(doc, "request", ""),
                "response": getattr(doc, "response", ""),
                "score": float(getattr(doc, "score", 0)),
            }
        matches.append(match_data)

    return {
        "input_query": user_query,
        "top_k": top_k,
        "results": matches,
    }

# -------------------------------
# CLI ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    print("\n--- Semantic Search CLI ---")
    print("Example: Validate login with username test and password 123\n")

    while True:
        user_input = input("Enter a query (or 'exit'): ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting...")
            break

        results = semantic_search(user_input, TOP_K)
        print(json.dumps(results, indent=2))
