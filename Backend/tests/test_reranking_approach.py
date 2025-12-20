"""
Test script to compare reranking approaches:
1. Current: Rerank based on query text only
2. Enhanced: Rerank based on query + API metadata

This tests whether including API metadata improves ranking accuracy.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.nlp.ranking_engine import (
    stage1_vector_retrieval,
    _get_reranker,
    _safe_float
)
from app.core.logger import logger


def rerank_with_metadata(user_query: str, candidates: list) -> list:
    """
    Enhanced Stage 2: Include API metadata in reranking text
    
    Text format: "{query} | API: {api} | {method} {endpoint}"
    """
    if not candidates:
        return []
    
    try:
        from flashrank import RerankRequest
        reranker = _get_reranker()
        
        passages = []
        for i, candidate in enumerate(candidates):
            # Build enhanced text with API metadata
            query_text = candidate.get("text", "").strip()
            api_name = candidate.get("api", "")
            endpoint = candidate.get("endpoint", "")
            method = candidate.get("method", "POST")
            
            # Enhanced text format
            enhanced_text = f"{query_text} | API: {api_name} | {method} {endpoint}"
            
            if query_text:
                passages.append({
                    "id": i,
                    "text": enhanced_text,
                    "meta": candidate
                })
        
        if not passages:
            return candidates
        
        rerank_request = RerankRequest(
            query=user_query,
            passages=passages
        )
        
        reranked_results = reranker.rerank(rerank_request)
        
        final_results = []
        for new_rank, result in enumerate(reranked_results, start=1):
            original_candidate = result.get("meta", candidates[result.get("id", 0)])
            final_results.append({
                "rank": new_rank,
                "score": _safe_float(result.get("score", 0.0)),
                "text": original_candidate.get("text", ""),  # Original text, not enhanced
                "api": original_candidate.get("api", ""),
                "endpoint": original_candidate.get("endpoint", ""),
                "method": original_candidate.get("method", "POST"),
            })
        
        return final_results
        
    except Exception as e:
        logger.error(f"Enhanced reranking failed: {e}")
        raise


def rerank_text_only(user_query: str, candidates: list) -> list:
    """Current Stage 2: Only query text for reranking"""
    if not candidates:
        return []
    
    try:
        from flashrank import RerankRequest
        reranker = _get_reranker()
        
        passages = []
        for i, candidate in enumerate(candidates):
            text = candidate.get("text", "").strip()
            if text:
                passages.append({
                    "id": i,
                    "text": text,
                    "meta": candidate
                })
        
        if not passages:
            return candidates
        
        rerank_request = RerankRequest(
            query=user_query,
            passages=passages
        )
        
        reranked_results = reranker.rerank(rerank_request)
        
        final_results = []
        for new_rank, result in enumerate(reranked_results, start=1):
            original_candidate = result.get("meta", candidates[result.get("id", 0)])
            final_results.append({
                "rank": new_rank,
                "score": _safe_float(result.get("score", 0.0)),
                "text": original_candidate.get("text", ""),
                "api": original_candidate.get("api", ""),
                "endpoint": original_candidate.get("endpoint", ""),
                "method": original_candidate.get("method", "POST"),
            })
        
        return final_results
        
    except Exception as e:
        logger.error(f"Text-only reranking failed: {e}")
        raise


def compare_approaches(test_query: str, top_k: int = 10):
    """Compare both reranking approaches"""
    print(f"\n{'='*70}")
    print(f"TEST QUERY: {test_query}")
    print(f"{'='*70}\n")
    
    # Stage 1: Get candidates
    print("📥 Stage 1: Vector Retrieval from Redis...")
    try:
        candidates = stage1_vector_retrieval(test_query, top_k=top_k)
        print(f"   Retrieved {len(candidates)} candidates\n")
    except Exception as e:
        print(f"❌ Stage 1 failed: {e}")
        print("   Make sure you have embeddings in Redis!")
        return
    
    if not candidates:
        print("❌ No candidates retrieved. Ensure embeddings exist in Redis.")
        return
    
    # Show Stage 1 results
    print("📊 STAGE 1 RESULTS (Vector Similarity Order):")
    print("-" * 50)
    for c in candidates[:5]:
        print(f"   #{c['rank']} | {c['api']:25} | Score: {c['vector_score']:.4f}")
        print(f"       Text: {c['text'][:60]}...")
    print()
    
    # Approach 1: Text only
    print("🔹 APPROACH 1: Rerank by QUERY TEXT ONLY")
    print("-" * 50)
    try:
        results_text_only = rerank_text_only(test_query, candidates)
        for r in results_text_only[:5]:
            print(f"   #{r['rank']} | {r['api']:25} | Score: {r['score']:.4f}")
            print(f"       Text: {r['text'][:60]}...")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        results_text_only = []
    
    # Approach 2: Text + Metadata
    print("🔹 APPROACH 2: Rerank by QUERY + API METADATA")
    print("-" * 50)
    try:
        results_with_metadata = rerank_with_metadata(test_query, candidates)
        for r in results_with_metadata[:5]:
            print(f"   #{r['rank']} | {r['api']:25} | Score: {r['score']:.4f}")
            print(f"       Text: {r['text'][:60]}...")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        results_with_metadata = []
    
    # Compare top results
    if results_text_only and results_with_metadata:
        print("📈 COMPARISON:")
        print("-" * 50)
        if results_text_only[0]['api'] == results_with_metadata[0]['api']:
            print(f"   ✅ Both approaches agree on #1: {results_text_only[0]['api']}")
        else:
            print(f"   ⚠️  Different #1 results:")
            print(f"      Text-only: {results_text_only[0]['api']}")
            print(f"      With metadata: {results_with_metadata[0]['api']}")
        
        # Score difference
        score_diff = results_with_metadata[0]['score'] - results_text_only[0]['score']
        print(f"   Score difference: {score_diff:+.4f}")


if __name__ == "__main__":
    # Test queries
    test_queries = [
        "Create a customer order with card payment",
        "Login with username and password",
        "Test user authentication",
        "Place an order using UPI",
    ]
    
    print("\n" + "=" * 70)
    print("RERANKING APPROACH COMPARISON TEST")
    print("Comparing: Text-Only vs Query+API-Metadata")
    print("=" * 70)
    
    for query in test_queries:
        try:
            compare_approaches(query, top_k=10)
        except Exception as e:
            print(f"\n❌ Test failed for '{query}': {e}")
