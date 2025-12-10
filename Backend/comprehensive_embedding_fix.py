"""Comprehensive fix for ALL corrupted embeddings in Redis"""
import numpy as np
from app.redis_config import get_redis_client
from app.nlp.embedding_model import get_model
import time

r = get_redis_client()
model = get_model()

print("=== COMPREHENSIVE EMBEDDING FIX ===")
print("Scanning ALL embeddings for any issues...\n")

cursor = 0
total = 0
fixed = 0
issues_found = []

while True:
    cursor, keys = r.scan(cursor, match='api:*', count=100)
    
    for key in keys:
        total += 1
        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
        
        try:
            embedding_bytes = r.hget(key, 'query_embedding')
            query_bytes = r.hget(key, 'query')
            query_str = query_bytes.decode('utf-8') if query_bytes else None
            
            needs_fix = False
            issue = ""
            
            if not embedding_bytes:
                needs_fix = True
                issue = "Missing embedding"
            else:
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                
                # Check for various issues
                if len(embedding) != 768:
                    needs_fix = True
                    issue = f"Wrong dimension: {len(embedding)}"
                elif np.isnan(embedding).any():
                    needs_fix = True
                    issue = f"Contains NaN: {np.isnan(embedding).sum()} values"
                elif np.isinf(embedding).any():
                    needs_fix = True
                    issue = f"Contains Inf: {np.isinf(embedding).sum()} values"
                elif np.linalg.norm(embedding) < 1e-6:
                    needs_fix = True
                    issue = "Zero norm (all zeros)"
                elif np.linalg.norm(embedding) < 0.9 or np.linalg.norm(embedding) > 1.1:
                    needs_fix = True
                    issue = f"Bad norm: {np.linalg.norm(embedding):.4f}"
            
            if needs_fix and query_str:
                issues_found.append({
                    'key': key_str[:60],
                    'query': query_str[:50],
                    'issue': issue
                })
                
                # Generate new embedding
                new_embedding = model.encode([query_str], normalize_embeddings=True)[0]
                new_norm = np.linalg.norm(new_embedding)
                
                if new_norm > 0.9 and new_norm < 1.1 and not np.isnan(new_embedding).any():
                    # Store back to Redis
                    embedding_bytes = new_embedding.astype(np.float32).tobytes()
                    r.hset(key_str, 'query_embedding', embedding_bytes)
                    fixed += 1
                    
                    if fixed <= 10:  # Only print first 10
                        print(f"✅ Fixed [{issue}]: {query_str[:50]}...")
                    elif fixed == 11:
                        print("... (more fixes in progress)")
                else:
                    print(f"❌ Could not fix: {query_str[:50]}... (new norm: {new_norm})")
                        
        except Exception as e:
            print(f"Error processing {key_str[:40]}: {e}")
    
    if cursor == 0:
        break
    
    # Progress indicator
    if total % 200 == 0:
        print(f"  Scanned {total} documents...")

print(f"\n=== SUMMARY ===")
print(f"Total documents scanned: {total}")
print(f"Issues found: {len(issues_found)}")
print(f"Successfully fixed: {fixed}")

if issues_found and len(issues_found) <= 20:
    print(f"\n=== Issues Found ===")
    for item in issues_found:
        print(f"  - {item['issue']}: {item['query']}")

# Verify fix
print(f"\n=== VERIFICATION ===")
cursor = 0
remaining_issues = 0
while True:
    cursor, keys = r.scan(cursor, match='api:*', count=100)
    for key in keys:
        emb = r.hget(key, 'query_embedding')
        if emb:
            arr = np.frombuffer(emb, dtype=np.float32)
            norm = np.linalg.norm(arr)
            if norm < 0.9 or norm > 1.1 or np.isnan(arr).any() or np.isinf(arr).any():
                remaining_issues += 1
    if cursor == 0:
        break

print(f"Remaining issues after fix: {remaining_issues}")
if remaining_issues == 0:
    print("✅ ALL EMBEDDINGS ARE NOW VALID!")
else:
    print(f"⚠️ Still have {remaining_issues} problematic embeddings")
