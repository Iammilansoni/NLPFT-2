import numpy as np
import json
from sentence_transformers import SentenceTransformer
from redis.commands.search.query import Query
from redis_config import get_redis_client
from sklearn.metrics.pairwise import cosine_similarity

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

    # Encode user query
    query_vec = model.encode([user_query], normalize_embeddings=True)
    query_vec_bytes = np.asarray(query_vec, dtype=np.float32).tobytes()

    # Search Redis
    q = (
        Query("*=>[KNN $k @query_embedding $vec AS score]")
        .sort_by("score")
        .return_fields("query", "api", "endpoint", "request", "response", "score", "query_embedding")
        .dialect(2)
    )

    params = {"vec": query_vec_bytes, "k": top_k}
    results = ft.search(q, query_params=params)

    # Process results and calculate cosine similarity
    matches = []
    for doc in results.docs:
        try:
            # Parse document data
            match_data = {
                "query": doc.query,
                "api": doc.api,
                "endpoint": doc.endpoint,
                "request": json.loads(doc.request) if doc.request else {},
                "response": json.loads(doc.response) if doc.response else {},
                "redis_score": float(doc.score),
            }
            
            # Calculate cosine similarity
            if hasattr(doc, 'query_embedding') and doc.query_embedding:
                # Convert stored embedding back to numpy array
                stored_vec = np.frombuffer(doc.query_embedding, dtype=np.float32).reshape(1, -1)
                query_vec_2d = query_vec.reshape(1, -1)
                
                # Calculate cosine similarity
                cos_sim = cosine_similarity(query_vec_2d, stored_vec)[0][0]
                match_data["cosine_similarity"] = float(cos_sim)
            else:
                match_data["cosine_similarity"] = None
                
        except Exception as e:
            match_data = {
                "query": getattr(doc, "query", ""),
                "api": getattr(doc, "api", ""),
                "endpoint": getattr(doc, "endpoint", ""),
                "request": getattr(doc, "request", ""),
                "response": getattr(doc, "response", ""),
                "redis_score": float(getattr(doc, "score", 0)),
                "cosine_similarity": None,
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
            print("🏆 TOP 1 RESULT:")
            print("="*60)
            print(f"Query: {top_1['query']}")
            print(f"API: {top_1['api']}")
            print(f"Endpoint: {top_1['endpoint']}")
            print(f"Redis Score: {top_1['redis_score']:.4f}")
            if top_1.get('cosine_similarity') is not None:
                print(f"Cosine Similarity: {top_1['cosine_similarity']:.4f} ({top_1['cosine_similarity']*100:.2f}%)")
            print(f"Request: {json.dumps(top_1['request'], indent=2)}")
            print(f"Response: {json.dumps(top_1['response'], indent=2)}")
        else:
            print("\n⚠️  No results found!")
