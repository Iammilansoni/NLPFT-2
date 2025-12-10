"""Test FlashRank scoring behavior"""
from flashrank import Ranker, RerankRequest
import numpy as np

r = Ranker('ms-marco-MiniLM-L-12-v2', cache_dir='/tmp/flashrank_cache')

query = "Login me with the credentials milan and milan123"

passages = [
    {'id': 0, 'text': 'access my account request for milan_s using secret pass123'},
    {'id': 1, 'text': 'please log me in: uname=user123, secret=Beta#456'},
    {'id': 2, 'text': 'login with username milan and password milan123'},
    {'id': 3, 'text': 'authenticate user with credentials'},
]

req = RerankRequest(query=query, passages=passages)
results = r.rerank(req)

print(f"Query: {query}\n")
print("Results:")
for i, res in enumerate(results):
    score = float(res['score'])
    print(f"  #{i+1}: score={score:.6f} ({score*100:.2f}%) - {res['text'][:60]}")
    print(f"       Raw score type: {type(res['score'])}, value: {res['score']}")
    print(f"       Is NaN: {np.isnan(score)}, Is Inf: {np.isinf(score)}")
