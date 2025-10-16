"""
Simple script to view and query Redis data
"""
import redis
from redis_config import get_redis_client
import numpy as np
from sentence_transformers import SentenceTransformer

def view_redis_stats():
    """View basic Redis statistics"""
    r = get_redis_client()
    
    print("=" * 60)
    print("Redis Database Statistics")
    print("=" * 60)
    
    # Get database info
    info = r.info('stats')
    print(f"\n📊 Total Keys: {r.dbsize()}")
    print(f"📥 Total Commands Processed: {info.get('total_commands_processed', 'N/A')}")
    print(f"💾 Memory Used: {r.info('memory').get('used_memory_human', 'N/A')}")
    
    # Count API records
    api_keys = list(r.scan_iter("api:*", count=100))
    print(f"\n🔍 Total API Records: {len(api_keys)}")
    
    return r, api_keys

def view_sample_records(r, api_keys, num_samples=5):
    """View sample records from Redis"""
    print("\n" + "=" * 60)
    print(f"Sample Records (showing {min(num_samples, len(api_keys))} records)")
    print("=" * 60)
    
    for i, key in enumerate(api_keys[:num_samples]):
        data = r.hgetall(key)
        print(f"\n📄 Record {i+1} - {key.decode() if isinstance(key, bytes) else key}")
        print(f"   Query: {data[b'query'].decode()[:100]}...")
        print(f"   API: {data[b'api'].decode()}")
        print(f"   Endpoint: {data[b'endpoint'].decode()}")
        print(f"   Request: {data[b'request'].decode()[:80]}...")
        print(f"   Response: {data[b'response'].decode()[:80]}...")

def search_redis(query_text, top_k=5):
    """Search Redis using vector similarity"""
    print("\n" + "=" * 60)
    print(f"Vector Search: '{query_text}'")
    print("=" * 60)
    
    r = get_redis_client()
    
    # Load model and create query embedding
    print("\n🔄 Loading embedding model...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    query_embedding = model.encode(query_text, normalize_embeddings=True)
    query_bytes = np.asarray(query_embedding, dtype=np.float32).tobytes()
    
    # Perform vector search
    from redis.commands.search.query import Query
    
    q = (
        Query(f"*=>[KNN {top_k} @query_embedding $vec AS score]")
        .return_fields("query", "api", "endpoint", "score")
        .sort_by("score")
        .dialect(2)
    )
    
    print(f"\n🔍 Searching for top {top_k} results...")
    results = r.ft("idx:apis").search(q, query_params={"vec": query_bytes})
    
    print(f"\n✅ Found {results.total} results:\n")
    for i, doc in enumerate(results.docs, 1):
        print(f"{i}. Query: {doc.query}")
        print(f"   API: {doc.api}")
        print(f"   Endpoint: {doc.endpoint}")
        print(f"   Score: {doc.score}")
        print()

def clear_redis_data():
    """Clear all data from Redis (USE WITH CAUTION!)"""
    r = get_redis_client()
    
    response = input("\n⚠️  WARNING: This will delete ALL data from Redis. Continue? (yes/no): ")
    if response.lower() == 'yes':
        r.flushdb()
        print("✅ Redis database cleared!")
    else:
        print("❌ Operation cancelled.")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Redis Data Viewer")
    print("=" * 60)
    
    # View stats
    r, api_keys = view_redis_stats()
    
    if len(api_keys) > 0:
        # View sample records
        view_sample_records(r, api_keys, num_samples=3)
        
        # Interactive menu
        while True:
            print("\n" + "=" * 60)
            print("Options:")
            print("=" * 60)
            print("1. View more sample records")
            print("2. Search by query (vector search)")
            print("3. View Redis stats again")
            print("4. Clear all Redis data")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                num = input("How many records to view? (default 5): ").strip()
                num = int(num) if num.isdigit() else 5
                view_sample_records(r, api_keys, num_samples=num)
            
            elif choice == "2":
                query = input("Enter your search query: ").strip()
                if query:
                    search_redis(query)
            
            elif choice == "3":
                r, api_keys = view_redis_stats()
            
            elif choice == "4":
                clear_redis_data()
                r, api_keys = view_redis_stats()
            
            elif choice == "5":
                print("\n👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please try again.")
    else:
        print("\n⚠️  No data found in Redis. Run database_generator.py first!")
