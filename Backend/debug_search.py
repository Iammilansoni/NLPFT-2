"""Debug vector search results"""
from JSONoutput_generator import encode_bytes, vector_search

query = "Please validate confedential avadhi and avdhi@123"
qvec = encode_bytes(query)
hits = vector_search(qvec, top_k=10)

print(f"Query: {query}\n")
print("Top 10 search results:")
print("="*70)

for i, hit in enumerate(hits, 1):
    print(f"{i}. API: {hit.get('api', 'N/A')}")
    print(f"   Query: {hit.get('query', 'N/A')[:80]}...")
    print(f"   Score: {hit.get('score', 'N/A')}")
    print()
