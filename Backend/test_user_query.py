"""Test the exact user query"""
import numpy as np
from app.redis_config import get_redis_client
from app.nlp.embedding_model import get_model
from redis.commands.search.query import Query

r = get_redis_client()
model = get_model()
ft = r.ft('idx:api')

# Test with the exact user query
query_text = "Test user login with the details of sanjay and pari21@"
print(f"Query: {query_text}\n")

# Generate query embedding
q_vec = model.encode([query_text], normalize_embeddings=True)
print(f"Query embedding shape: {q_vec.shape}")
print(f"Query embedding has NaN: {np.isnan(q_vec).any()}")
print(f"Query embedding norm: {np.linalg.norm(q_vec[0]):.4f}")

# Convert to bytes
q_bytes = np.asarray(q_vec, dtype=np.float32).tobytes()
print(f"Query bytes length: {len(q_bytes)}")

# Search
q = (
    Query("*=>[KNN $k @query_embedding $vec AS vector_score]")
    .sort_by("vector_score")
    .return_fields("query", "api", "endpoint", "vector_score")
    .dialect(2)
)

params = {"vec": q_bytes, "k": 10}

try:
    results = ft.search(q, query_params=params)
    print(f"\nTotal results: {results.total}")
    
    for i, doc in enumerate(results.docs, 1):
        score_raw = getattr(doc, 'vector_score', 'N/A')
        query_doc = getattr(doc, 'query', 'N/A')[:60]
        
        print(f"\n#{i}: raw_score={score_raw}")
        print(f"    query={query_doc}")
        
        try:
            distance = float(score_raw)
            similarity = 1.0 - distance
            print(f"    parsed: distance={distance:.4f}, similarity={similarity:.4f} ({similarity*100:.1f}%)")
        except Exception as e:
            print(f"    parse error: {e}")
            
except Exception as e:
    print(f"Search error: {e}")
    import traceback
    traceback.print_exc()
