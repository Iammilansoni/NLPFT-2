"""
Fix Redis index - Drop and recreate with correct field name
"""
import redis
from app.core.logger import logger

def fix_index():
    r = redis.Redis(host='localhost', port=6379, decode_responses=False)
    
    try:
        # Drop the old index (but keep the data)
        logger.info("Dropping old index...")
        r.ft('idx:api').dropindex(delete_documents=False)
        logger.info("✅ Old index dropped (data preserved)")
    except Exception as e:
        logger.warning(f"Could not drop index: {e}")
    
    # Recreate index with correct field name
    logger.info("Recreating index with correct field name...")
    from app.nlp.embedding_manager import get_embedding_manager
    
    # This will create the index
    embedder = get_embedding_manager()
    
    # Verify
    stats = embedder.get_stats()
    logger.info(f"✅ Index recreated!")
    logger.info(f"   Total documents: {stats.get('total_documents')}")
    logger.info(f"   Intents: {list(stats.get('intents', {}).keys())}")
    
    # Test search
    logger.info("\n🔍 Testing search...")
    results = embedder.search("Login with credentials", top_k=3)
    logger.info(f"✅ Found {len(results)} results")
    for i, r in enumerate(results[:3], 1):
        logger.info(f"   {i}. {r['query'][:60]} (similarity: {r['similarity']:.3f})")

if __name__ == "__main__":
    fix_index()
