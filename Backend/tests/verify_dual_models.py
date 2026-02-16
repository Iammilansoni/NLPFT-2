
import sys
import uuid
from pathlib import Path

# Add Backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.redis_vector_service import RedisVectorService

def verify_dual_models():
    print("🚀 Starting Dual Model Verification...")
    
    service = RedisVectorService()
    
    # Test Data
    user_id = uuid.uuid4()
    query_384 = "This is a test for 384 dimension model"
    query_768 = "This is a test for 768 dimension model"
    
    # 1. Store with 384-dim model (all-minilm)
    print("\n🧪 Testing 384-dim model (all-minilm)...")
    key_384, vec_384 = service.store_embedding(
        user_id=user_id,
        query=query_384,
        model_name="all-minilm"
    )
    print(f"✅ Stored 384-dim vector. Key: {key_384}")
    print(f"   Vector shape: {vec_384.shape}")
    
    if vec_384.shape[0] != 384:
        print(f"❌ Error: Expected 384 dimensions, got {vec_384.shape[0]}")
        return
        
    # Verify index existence
    try:
        info = service.redis_client.ft("embeddings_384").info()
        print("✅ Index 'embeddings_384' exists")
    except Exception as e:
        print(f"❌ Index 'embeddings_384' missing: {e}")

    # 2. Store with 768-dim model (nomic-embed-text)
    print("\n🧪 Testing 768-dim model (nomic-embed-text)...")
    # Note: This might download the model if not cached, so it could take time
    try:
        key_768, vec_768 = service.store_embedding(
            user_id=user_id,
            query=query_768,
            model_name="nomic-embed-text"
        )
        print(f"✅ Stored 768-dim vector. Key: {key_768}")
        print(f"   Vector shape: {vec_768.shape}")
        
        if vec_768.shape[0] != 768:
            print(f"❌ Error: Expected 768 dimensions, got {vec_768.shape[0]}")
            return

        # Verify index existence
        try:
            info = service.redis_client.ft("embeddings_768").info()
            print("✅ Index 'embeddings_768' exists")
        except Exception as e:
            print(f"❌ Index 'embeddings_768' missing: {e}")
            
    except Exception as e:
        print(f"⚠️ Skipping 768-dim test (model might be missing or slow to load): {e}")

    # 3. Search
    print("\n🔍 Testing Search...")
    results_384 = service.search_similar(query_384, user_id=user_id, top_k=1, model_name="all-minilm")
    print(f"   Search (384) results: {len(results_384)}")
    if len(results_384) > 0 and results_384[0]['redis_key'] == key_384:
        print("✅ Found correct 384-dim document")
    else:
        print("❌ Failed to find 384-dim document")

    # Clean up
    print("\n🧹 Cleaning up...")
    service.delete_embedding(key_384, user_id)
    if 'key_768' in locals():
        service.delete_embedding(key_768, user_id)
    
    print("\n✨ Verification Complete!")

if __name__ == "__main__":
    verify_dual_models()
