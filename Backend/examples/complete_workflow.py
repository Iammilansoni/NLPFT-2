
import asyncio
import json
from pathlib import Path
from datetime import datetime

from app.services.embedding_service import get_embedding_service
from app.services.dataset_service import get_dataset_service

SAMPLE_DATASET = {
    "project": {
        "name": "AI Automation Dataset",
        "base_url": "https://api.example.com",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "vector_similarity": "cosine"
    },
    "datasets": [
        {
            "api": "login",
            "endpoint": "https://api.example.com/api/login",
            "request": {
                "username": "demo_user",
                "password": "demo_pass"
            },
            "response": {
                "definition": "Authenticates a user using provided username and password"
            },
            "paraphrase_type": "login_synonyms_fuzzy_tone",
            "nl_inputs": [
                {"id": 0, "text": "login using username and password", "token_count": 6, "char_count": 34, "style": "synonym"},
                {"id": 1, "text": "sign in with credentials", "token_count": 5, "char_count": 24, "style": "synonym"},
                {"id": 2, "text": "authenticate with my username and password", "token_count": 7, "char_count": 42, "style": "synonym"},
                {"id": 3, "text": "please log in with my creds", "token_count": 7, "char_count": 27, "style": "polite"},
                {"id": 4, "text": "access my account using credentials", "token_count": 6, "char_count": 35, "style": "synonym"},
                {"id": 5, "text": "logn with my credentails", "token_count": 5, "char_count": 24, "style": "typo"},
                {"id": 6, "text": "signin with usrname and pasword", "token_count": 6, "char_count": 31, "style": "typo"},
                {"id": 7, "text": "log in to the system", "token_count": 6, "char_count": 20, "style": "contextual"},
                {"id": 8, "text": "authenticate using credentials", "token_count": 4, "char_count": 30, "style": "imperative"},
                {"id": 9, "text": "login user123/pass123", "token_count": 3, "char_count": 21, "style": "shorthand"},
                {"id": 10, "text": "with username X, sign in", "token_count": 6, "char_count": 24, "style": "order-variant"},
                {"id": 11, "text": "authorize me with my login details", "token_count": 7, "char_count": 34, "style": "synonym"},
                {"id": 12, "text": "let me in using my username and password", "token_count": 9, "char_count": 40, "style": "declarative"},
                {"id": 13, "text": "please grant access after verifying credentials", "token_count": 7, "char_count": 48, "style": "polite"},
                {"id": 14, "text": "start a session using my credentials", "token_count": 7, "char_count": 36, "style": "contextual"}
            ],
            "chunks": [],
            "redis_meta": {
                "index": "automation:intents",
                "key_prefix": "api:",
                "vector_field": "embedding",
                "text_field": "text",
                "meta_fields": ["api", "endpoint", "style", "chunk_id", "paraphrase_id"]
            }
        },
        {
            "api": "logout",
            "endpoint": "https://api.example.com/api/logout",
            "request": {
                "token": "access_token_example"
            },
            "response": {
                "definition": "Terminates the current authenticated session"
            },
            "paraphrase_type": "logout_synonyms_fuzzy_tone",
            "nl_inputs": [
                {"id": 0, "text": "log me out of my account", "token_count": 7, "char_count": 24, "style": "synonym"},
                {"id": 1, "text": "sign out from this session", "token_count": 6, "char_count": 26, "style": "synonym"},
                {"id": 2, "text": "please end my login session", "token_count": 6, "char_count": 27, "style": "polite"},
                {"id": 3, "text": "logout now", "token_count": 2, "char_count": 10, "style": "imperative"},
                {"id": 4, "text": "terminate the active session", "token_count": 5, "char_count": 28, "style": "synonym"},
                {"id": 5, "text": "kindly sign me out", "token_count": 4, "char_count": 18, "style": "polite"},
                {"id": 6, "text": "exit the portal", "token_count": 3, "char_count": 15, "style": "contextual"},
                {"id": 7, "text": "end authentication", "token_count": 2, "char_count": 18, "style": "synonym"},
                {"id": 8, "text": "log off from the dashboard", "token_count": 6, "char_count": 26, "style": "contextual"},
                {"id": 9, "text": "signout from the system", "token_count": 5, "char_count": 23, "style": "typo"},
                {"id": 10, "text": "please close my session", "token_count": 5, "char_count": 23, "style": "polite"},
                {"id": 11, "text": "invalidate my access token", "token_count": 5, "char_count": 26, "style": "synonym"},
                {"id": 12, "text": "sign me off from the portal", "token_count": 7, "char_count": 27, "style": "contextual"},
                {"id": 13, "text": "pls loggout", "token_count": 2, "char_count": 11, "style": "typo"},
                {"id": 14, "text": "end my session safely", "token_count": 4, "char_count": 21, "style": "declarative"}
            ],
            "chunks": [],
            "redis_meta": {
                "index": "automation:intents",
                "key_prefix": "api:",
                "vector_field": "embedding",
                "text_field": "text",
                "meta_fields": ["api", "endpoint", "style", "chunk_id", "paraphrase_id"]
            }
        }
    ]
}


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


async def main():
    
    print_section("🚀 Synthetic Dataset Generation - Complete Workflow Example")
    
    print_section("Step 1: Initialize Services")
    
    embedding_service = get_embedding_service()
    dataset_service = get_dataset_service(redis_url="redis://localhost:6379")
    
    print("✅ Embedding Service initialized")
    print(f"   Model: {embedding_service.MODEL_NAME}")
    print(f"   Vector Dimension: {embedding_service.VECTOR_DIM}")
    print(f"   Device: {embedding_service.device}")
    
    print("\n✅ Dataset Service initialized")
    print(f"   Redis URL: {dataset_service.redis_url}")
    print(f"   Index Name: {dataset_service.index_name}")
    
    print_section("Step 2: Create Chunks from Paraphrases")
    
    dataset = SAMPLE_DATASET.copy()
    
    for api_data in dataset["datasets"]:
        api = api_data["api"]
        nl_inputs = api_data["nl_inputs"]
        
        print(f"Processing API: {api}")
        print(f"  Paraphrases: {len(nl_inputs)}")
        
        texts = [inp["text"] for inp in nl_inputs]
        
        chunks = embedding_service.chunk_texts(
            texts,
            target_min_tokens=50,
            target_max_tokens=100
        )
        
        api_data["chunks"] = chunks
        
        print(f"  Chunks created: {len(chunks)}")
        for chunk in chunks:
            print(f"    - Chunk {chunk['chunk_id']}: {chunk['approx_token_count']} tokens, "
                  f"{len(chunk['paraphrase_ids'])} paraphrases")
    
    print_section("Step 3: Generate Embeddings for Chunks")
    
    for api_data in dataset["datasets"]:
        api = api_data["api"]
        chunks = api_data["chunks"]
        
        print(f"Generating embeddings for API: {api}")
        
        enriched_chunks = embedding_service.embed_chunks(chunks)
        api_data["chunks"] = enriched_chunks
        
        print(f"  ✅ Generated {len(enriched_chunks)} embeddings")
        
        if enriched_chunks:
            first_chunk = enriched_chunks[0]
            embedding = first_chunk["embedding"]
            print(f"  Sample embedding shape: ({len(embedding)},)")
            print(f"  Sample embedding (first 5 values): {embedding[:5]}")
    
    print_section("Step 4: Store Dataset in Redis Vector DB")
    
    try:
        print("Creating Redis vector index...")
        dataset_service.create_vector_index(force_recreate=True)
        print("✅ Index created successfully")
        
        print("\nStoring dataset with embeddings...")
        stats = dataset_service.store_dataset_in_redis(dataset, embed_chunks=False)
        
        print("✅ Dataset stored in Redis")
        print(f"  APIs stored: {stats['apis_stored']}")
        print(f"  Chunks stored: {stats['chunks_stored']}")
        print(f"  Paraphrases: {stats['paraphrases_stored']}")
        print(f"  Embeddings generated: {stats['embeddings_generated']}")
        
    except Exception as e:
        print(f"⚠️  Redis storage failed (make sure Redis is running): {e}")
        print("   Continuing with export generation...")
    
    print_section("Step 5: Export Dataset to JSONL and CSV")
    
    output_dir = Path("./exports")
    output_dir.mkdir(exist_ok=True)
    
    export_files = dataset_service.generate_export_files(dataset, output_dir)
    
    print("✅ Files exported successfully:")
    print(f"  JSONL: {export_files['jsonl']}")
    print(f"  CSV: {export_files['csv']}")
    print(f"  Timestamp: {export_files['timestamp']}")
    
    jsonl_path = Path(export_files['jsonl'])
    if jsonl_path.exists():
        lines = jsonl_path.read_text(encoding='utf-8').split('\n')
        print(f"\n  Sample JSONL (first 3 lines):")
        for line in lines[:3]:
            if line:
                data = json.loads(line)
                print(f"    {data['api']}: {data['text'][:50]}...")
    
    print_section("Step 6: Test Semantic Search")
    
    try:
        test_queries = [
            "sign me in with my password",
            "I want to log out",
            "authenticate me please"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = dataset_service.search_similar_intents(query, top_k=3)
            
            print(f"  Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"    {i}. {result['api']} (score: {result['similarity_score']:.3f})")
                print(f"       Text: {result['text'][:80]}...")
    
    except Exception as e:
        print(f"⚠️  Semantic search failed (Redis not available): {e}")
    
    print_section("Step 7: Get Redis Statistics")
    
    try:
        stats = dataset_service.get_stats()
        
        print("📊 Redis Statistics:")
        print(f"  Index Name: {stats.get('index_name', 'N/A')}")
        print(f"  Total Documents: {stats.get('total_documents', 0)}")
        print(f"  Total Keys: {stats.get('total_keys', 0)}")
        print(f"  Embedding Model: {stats.get('embedding_model', 'N/A')}")
        print(f"  Vector Dimension: {stats.get('vector_dim', 0)}")
    
    except Exception as e:
        print(f"⚠️  Could not get statistics: {e}")
    
    print_section("✨ Workflow Complete!")
    
    print("Summary:")
    print(f"  ✅ Processed {len(dataset['datasets'])} APIs")
    print(f"  ✅ Generated embeddings for all chunks")
    print(f"  ✅ Exported to JSONL and CSV")
    print(f"  ✅ Stored in Redis (if available)")
    print(f"  ✅ Tested semantic search")
    
    print("\nNext steps:")
    print("  1. Check the export files in ./exports/")
    print("  2. Use the JSONL file for training/fine-tuning")
    print("  3. Use the CSV file for data analysis")
    print("  4. Query Redis for semantic search")
    print("  5. Integrate with your AI automation pipeline")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
