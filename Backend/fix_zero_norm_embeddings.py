"""Find and fix zero-norm embeddings in Redis"""
import numpy as np
from app.redis_config import get_redis_client
from app.nlp.embedding_model import get_model

r = get_redis_client()
model = get_model()

# Find all zero-norm embeddings
print("=== Scanning for zero-norm embeddings ===")
cursor = 0
zero_norm_keys = []
total = 0

while True:
    cursor, keys = r.scan(cursor, match='api:*', count=100)
    
    for key in keys:
        total += 1
        embedding_bytes = r.hget(key, 'query_embedding')
        
        if embedding_bytes:
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            norm_val = np.linalg.norm(embedding)
            
            if norm_val < 1e-6:  # Effectively zero
                query = r.hget(key, 'query')
                query_str = query.decode('utf-8') if isinstance(query, bytes) else query
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                zero_norm_keys.append((key_str, query_str))
                print(f"  Found: {key_str[:50]}...")
                print(f"    Query: {query_str[:60] if query_str else 'N/A'}")
                print(f"    Norm: {norm_val}")
    
    if cursor == 0:
        break

print(f"\nTotal documents: {total}")
print(f"Zero-norm embeddings: {len(zero_norm_keys)}")

if zero_norm_keys:
    print("\n=== Regenerating embeddings for corrupted entries ===")
    
    for key_str, query_str in zero_norm_keys:
        if query_str:
            # Generate new embedding
            new_embedding = model.encode([query_str], normalize_embeddings=True)[0]
            new_norm = np.linalg.norm(new_embedding)
            
            print(f"\nFixing: {key_str[:60]}...")
            print(f"  Query: {query_str[:50]}")
            print(f"  New norm: {new_norm:.4f}")
            
            if new_norm > 0.9:  # Valid normalized embedding
                # Store back to Redis
                embedding_bytes = new_embedding.astype(np.float32).tobytes()
                r.hset(key_str, 'query_embedding', embedding_bytes)
                print(f"  ✅ Fixed!")
            else:
                print(f"  ❌ Still invalid, skipping")
    
    print("\n=== Done! Verify by running debug_vector_search.py again ===")
else:
    print("\nNo zero-norm embeddings found - the issue may be elsewhere.")
