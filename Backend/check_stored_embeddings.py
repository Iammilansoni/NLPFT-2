"""Check stored embeddings dimensions and compare with query"""
import numpy as np
from app.redis_config import get_redis_client
from app.nlp.embedding_model import get_model

r = get_redis_client()
model = get_model()

# Get a few stored embeddings
cursor = 0
cursor, keys = r.scan(cursor, match='api:*', count=10)

print("=== Checking stored embeddings ===")
for key in keys[:5]:
    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
    embedding_bytes = r.hget(key, 'query_embedding')
    query = r.hget(key, 'query')
    query_str = query.decode('utf-8')[:50] if query else 'N/A'
    
    if embedding_bytes:
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        print(f"\n{key_str}:")
        print(f"  Query: {query_str}")
        print(f"  Embedding dim: {len(embedding)}")
        print(f"  Has NaN: {np.isnan(embedding).any()}")
        print(f"  Has Inf: {np.isinf(embedding).any()}")
        print(f"  Norm: {np.linalg.norm(embedding):.4f}")
        print(f"  First 5: {embedding[:5]}")

# Generate query embedding
print("\n=== Query embedding ===")
query_emb = model.encode(["login"], normalize_embeddings=True)[0]
print(f"Query embedding dim: {len(query_emb)}")
print(f"Query has NaN: {np.isnan(query_emb).any()}")
print(f"Query norm: {np.linalg.norm(query_emb):.4f}")
print(f"Query first 5: {query_emb[:5]}")

# Check if dimensions match
stored_dim = len(np.frombuffer(r.hget(keys[0], 'query_embedding'), dtype=np.float32))
query_dim = len(query_emb)
print(f"\n=== Dimension Check ===")
print(f"Stored dimension: {stored_dim}")
print(f"Query dimension: {query_dim}")
print(f"Match: {stored_dim == query_dim}")
