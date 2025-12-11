"""Debug vector search to find NaN issue"""
from app.redis_config import get_redis_client
from redis.commands.search.query import Query
import numpy as np
from app.nlp.embedding_model import get_model

# Get model and redis
model = get_model()
r = get_redis_client()
ft = r.ft('idx:api')

# Check index info
print("=== Index Info ===")
try:
    info = ft.info()
    print(f"Index name: {info.get('index_name', 'N/A')}")
    print(f"Num docs: {info.get('num_docs', 'N/A')}")
    
    # Find vector field info
    for attr in info.get('attributes', []):
        print(f"Attribute: {attr}")
except Exception as e:
    print(f"Error getting index info: {e}")

# Encode query
print("\n=== Query Encoding ===")
query_text = "login"
q_vec = model.encode([query_text], normalize_embeddings=True)
print(f"Query vector shape: {q_vec.shape}")
print(f"Query vector dtype: {q_vec.dtype}")
print(f"Query vector first 5: {q_vec[0][:5]}")

# Try search with proper syntax
print("\n=== Vector Search ===")
try:
    q_bytes = np.asarray(q_vec, dtype=np.float32).tobytes()
    
    # Use correct KNN syntax
    q = (
        Query("*=>[KNN $k @query_embedding $vec AS vector_score]")
        .sort_by("vector_score")
        .return_fields("query", "api", "endpoint", "vector_score")
        .dialect(2)
    )
    
    params = {"vec": q_bytes, "k": 5}
    results = ft.search(q, query_params=params)
    
    print(f"Total results: {results.total}")
    for i, doc in enumerate(results.docs):
        score = getattr(doc, 'vector_score', 'N/A')
        query = getattr(doc, 'query', 'N/A')[:50]
        print(f"  #{i+1}: score={score} (type={type(score).__name__})")
        print(f"       query={query}")
        
        # Try to parse the score
        try:
            float_score = float(score)
            similarity = 1.0 - float_score
            print(f"       parsed: distance={float_score}, similarity={similarity}")
        except Exception as e:
            print(f"       parse error: {e}")
        
except Exception as e:
    print(f"Search error: {e}")
    import traceback
    traceback.print_exc()
