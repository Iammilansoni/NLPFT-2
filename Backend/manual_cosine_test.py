"""Direct cosine similarity test bypassing Redis KNN"""
import numpy as np
from app.redis_config import get_redis_client
from app.nlp.embedding_model import get_model
from numpy.linalg import norm

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

r = get_redis_client()
model = get_model()

# Generate query embedding
query_text = "login"
query_emb = model.encode([query_text], normalize_embeddings=True)[0]

# Get stored embeddings and compute cosine similarity manually
cursor = 0
results = []

print(f"Query: {query_text}")
print("Computing cosine similarity manually...\n")

cursor, keys = r.scan(cursor, match='api:*', count=50)
for key in keys:
    embedding_bytes = r.hget(key, 'query_embedding')
    query_str = r.hget(key, 'query')
    
    if embedding_bytes and query_str:
        stored_emb = np.frombuffer(embedding_bytes, dtype=np.float32)
        query_decoded = query_str.decode('utf-8') if isinstance(query_str, bytes) else query_str
        
        # Compute cosine similarity
        sim = cosine_similarity(query_emb, stored_emb)
        
        # Cosine distance = 1 - similarity (what Redis returns)
        dist = 1 - sim
        
        results.append({
            'query': query_decoded[:60],
            'similarity': sim,
            'distance': dist,
            'has_nan': np.isnan(sim)
        })

# Sort by similarity
results.sort(key=lambda x: x['similarity'], reverse=True)

print("Top 10 by manual cosine similarity:")
for i, r in enumerate(results[:10], 1):
    print(f"  #{i}: sim={r['similarity']:.4f} ({r['similarity']*100:.1f}%) dist={r['distance']:.4f}")
    print(f"      {r['query']}")

# Check for any NaN
nan_count = sum(1 for r in results if r['has_nan'])
print(f"\nResults with NaN: {nan_count} / {len(results)}")
