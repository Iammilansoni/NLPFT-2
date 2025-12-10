"""Test exact user query through API"""
import requests

query = "Test user login with the details of sanjay and pari21@"
r = requests.post('http://localhost:8000/api/v1/ranking/rank/detailed', json={'query': query, 'top_k': 5})

print(f"Status: {r.status_code}")
data = r.json()

print(f"\nQuery: {query}")
print(f"\nStage 1 (Vector Search) scores:")
for item in data.get('stage1_results', []):
    print(f"  {item['rank']}. vector_score={item['vector_score']:.4f} ({item['vector_score']*100:.1f}%) - {item['text'][:50]}")

print(f"\nStage 2 (FlashRank) scores:")
for item in data.get('ranked_results', [])[:5]:
    print(f"  {item['rank']}. score={item['score']:.4f} ({item['score']*100:.1f}%) - {item['text'][:50]}")
