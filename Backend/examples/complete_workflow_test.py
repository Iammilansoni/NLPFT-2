"""
Complete Workflow Example - NLPForge Intelligent API Testing Pipeline

This script demonstrates the full pipeline:
1. Parse natural language query
2. Generate smart dataset with Gemini
3. Embed to Redis vector database
4. Perform semantic search
5. Return best API match with confidence
"""

import requests
import json
import time
from typing import Dict

# Base URL for the API
BASE_URL = "http://localhost:8000"


def test_query(query: str, generate_dataset: bool = True, num_examples: int = 50, top_k: int = 5) -> Dict:
    """
    Test the complete pipeline with a natural language query
    
    Args:
        query: Natural language query
        generate_dataset: Whether to generate dataset if needed
        num_examples: Number of examples to generate
        top_k: Number of similar results to return
        
    Returns:
        Response dictionary
    """
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print(f"{'='*80}\n")
    
    # Make request
    url = f"{BASE_URL}/api/v1/query"
    payload = {
        "query": query,
        "generate_dataset": generate_dataset,
        "num_examples": num_examples,
        "top_k": top_k
    }
    
    start_time = time.time()
    response = requests.post(url, json=payload)
    elapsed = time.time() - start_time
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
        return {}
    
    result = response.json()
    
    # Display results
    print(f"✅ Success! (took {elapsed:.2f}s)\n")
    
    print(f"📌 Intent: {result['intent']}")
    print(f"📊 Confidence: {result['confidence']:.2%}")
    print(f"🔑 Slots: {json.dumps(result['slots'], indent=2)}")
    
    print(f"\n🎯 Best Matches:")
    for i, match in enumerate(result['best_matches'], 1):
        print(f"  {i}. {match['api']} - Score: {match['score']:.2%}")
    
    if result['dataset_generated']:
        print(f"\n📁 Dataset Generated:")
        info = result['dataset_info']
        print(f"  - Total Examples: {info['total_examples']}")
        print(f"  - Base Examples: {info['base_examples']}")
        print(f"  - Generated: {info['generated_examples']}")
        print(f"  - CSV: {info['paths']['csv']}")
        print(f"  - Embedded to Redis: {info.get('redis_keys', 0)} keys")
    
    print(f"\n🔍 Top Search Results:")
    for i, res in enumerate(result['search_results'][:3], 1):
        print(f"  {i}. Query: \"{res['query']}\"")
        print(f"     Intent: {res['intent']}")
        print(f"     Similarity: {res['similarity']:.2%}")
    
    return result


def get_stats() -> Dict:
    """Get database statistics"""
    url = f"{BASE_URL}/api/v1/stats"
    response = requests.get(url)
    
    if response.status_code == 200:
        stats = response.json()
        
        print(f"\n{'='*80}")
        print(f"DATABASE STATISTICS")
        print(f"{'='*80}\n")
        
        print(f"Index Name: {stats['index_name']}")
        print(f"Total Documents: {stats['total_documents']}")
        print(f"Embedding Model: {stats['model_name']}")
        print(f"Embedding Dimension: {stats['embedding_dimension']}")
        
        print(f"\nDocuments by Intent:")
        for intent, count in stats['intents'].items():
            print(f"  - {intent}: {count}")
        
        return stats
    else:
        print(f"❌ Error getting stats: {response.status_code}")
        return {}


def main():
    """Run complete workflow examples"""
    
    print("\n" + "="*80)
    print("NLPForge - Intelligent API Testing Pipeline")
    print("Complete Workflow Demonstration")
    print("="*80)
    
    # Check if API is running
    try:
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            print(f"❌ API not responding at {BASE_URL}")
            return
    except:
        print(f"❌ Cannot connect to API at {BASE_URL}")
        print("Please start the API first: python -m app.main")
        return
    
    # Test cases
    test_cases = [
        {
            "query": "Authenticate my credentials for Milan and MS3ESD",
            "description": "Login with username and password"
        },
        {
            "query": "Create a new account for john_doe with email john@example.com and password Test@123",
            "description": "Signup with multiple fields"
        },
        {
            "query": "Update my profile information for user milan",
            "description": "Update user profile"
        },
        {
            "query": "Delete account for user test_user",
            "description": "Delete user account"
        },
        {
            "query": "Get user information for admin",
            "description": "Retrieve user data"
        },
        {
            "query": "I forgot my password for milan@example.com",
            "description": "Password reset request"
        }
    ]
    
    # Run test cases
    results = []
    for test_case in test_cases:
        print(f"\n\n{'='*80}")
        print(f"TEST CASE: {test_case['description']}")
        print(f"{'='*80}")
        
        result = test_query(
            query=test_case['query'],
            generate_dataset=True,
            num_examples=30,
            top_k=5
        )
        results.append(result)
        
        # Wait a bit between requests
        time.sleep(1)
    
    # Get final statistics
    get_stats()
    
    # Summary
    print(f"\n\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"Total Queries Tested: {len(results)}")
    
    successful = sum(1 for r in results if r.get('intent') != 'unknown')
    print(f"Successful Detections: {successful}/{len(results)}")
    
    avg_confidence = sum(r.get('confidence', 0) for r in results) / len(results) if results else 0
    print(f"Average Confidence: {avg_confidence:.2%}")
    
    datasets_generated = sum(1 for r in results if r.get('dataset_generated', False))
    print(f"Datasets Generated: {datasets_generated}")
    
    print(f"\n✅ Workflow completed successfully!")


if __name__ == "__main__":
    main()
