"""Find and report corrupted embeddings in Redis"""
from app.redis_config import get_redis_client
import numpy as np
import struct

r = get_redis_client()
ft = r.ft('idx:api')

# Get all keys
print("=== Scanning for corrupted embeddings ===")
cursor = 0
corrupted = []
valid = []
total = 0

while True:
    cursor, keys = r.scan(cursor, match='api:*', count=100)
    
    for key in keys:
        total += 1
        try:
            # Get the embedding
            embedding_bytes = r.hget(key, 'query_embedding')
            if embedding_bytes:
                # Parse as float32 array
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                
                # Check for NaN or Inf
                has_nan = np.isnan(embedding).any()
                has_inf = np.isinf(embedding).any()
                
                if has_nan or has_inf:
                    query = r.hget(key, 'query')
                    if query:
                        query = query.decode('utf-8') if isinstance(query, bytes) else query
                    corrupted.append({
                        'key': key.decode('utf-8') if isinstance(key, bytes) else key,
                        'query': query[:50] if query else 'N/A',
                        'has_nan': has_nan,
                        'has_inf': has_inf,
                        'nan_count': np.isnan(embedding).sum(),
                        'inf_count': np.isinf(embedding).sum(),
                    })
                else:
                    valid.append(key)
            else:
                # No embedding at all
                query = r.hget(key, 'query')
                if query:
                    query = query.decode('utf-8') if isinstance(query, bytes) else query
                corrupted.append({
                    'key': key.decode('utf-8') if isinstance(key, bytes) else key,
                    'query': query[:50] if query else 'N/A',
                    'has_nan': False,
                    'has_inf': False,
                    'nan_count': 0,
                    'inf_count': 0,
                    'missing': True
                })
        except Exception as e:
            print(f"Error processing {key}: {e}")
    
    if cursor == 0:
        break

print(f"\nTotal documents: {total}")
print(f"Valid embeddings: {len(valid)}")
print(f"Corrupted/missing embeddings: {len(corrupted)}")

if corrupted:
    print(f"\n=== First 10 Corrupted Entries ===")
    for i, entry in enumerate(corrupted[:10]):
        print(f"  {i+1}. {entry['key']}")
        print(f"     Query: {entry['query']}")
        if entry.get('missing'):
            print(f"     Issue: Missing embedding")
        else:
            print(f"     Issue: NaN count={entry['nan_count']}, Inf count={entry['inf_count']}")
