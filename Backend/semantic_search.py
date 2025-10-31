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
        
        # Print all results
        print("\n" + "="*60)
        print("ALL TOP 5 RESULTS:")
        print("="*60)
        print(json.dumps(results, indent=2))
        
        # Print only top 1 result
        if results["results"]:
            top_1 = results["results"][0]
            print("\n" + "="*60)
            print("TOP 1 RESULT:")
            print("="*60)
            print(f"Query: {top_1['query']}")
            print(f"API: {top_1['api']}")
            print(f"Endpoint: {top_1['endpoint']}")
            print(f"Cosine Distance: {top_1['cosine_distance']:.4f} (lower is better)")
            print(f"Cosine Similarity: {top_1['cosine_similarity']:.4f} ({top_1['cosine_similarity']*100:.2f}%)")
            print(f"Request: {json.dumps(top_1['request'], indent=2)}")
            print(f"Response: {json.dumps(top_1['response'], indent=2)}")
        else:
            print("\n No results found!")
