"""
Quick test script to verify search functionality
"""
import asyncio
from app.nlp.embedding_manager import get_embedding_manager
from app.core.logger import logger

async def test_search():
    logger.info("=" * 60)
    logger.info("Testing Search Functionality")
    logger.info("=" * 60)
    
    # Get embedding manager
    embedder = get_embedding_manager()
    
    # Get stats
    stats = embedder.get_stats()
    logger.info(f"\n📊 Redis Stats:")
    logger.info(f"   Index: {stats.get('index_name')}")
    logger.info(f"   Total documents: {stats.get('total_documents')}")
    logger.info(f"   Embedding dimension: {stats.get('embedding_dimension')}")
    logger.info(f"   Intents: {stats.get('intents')}")
    
    if stats.get('total_documents', 0) == 0:
        logger.warning("\n⚠️  No documents in Redis!")
        logger.info("Loading csv_dataset.csv...")
        from app.nlp.dataset_ingestor import ingest_csv_to_redis
        result = ingest_csv_to_redis("csv_dataset.csv")
        if result.get("success"):
            logger.info(f"✅ Loaded {result.get('count')} embeddings")
        else:
            logger.error(f"❌ Failed: {result.get('error')}")
            return
    
    # Test search
    test_query = "Login with the credentials milan and milan123"
    logger.info(f"\n🔍 Testing search: '{test_query}'")
    
    results = embedder.search(test_query, top_k=5)
    
    logger.info(f"\n✅ Found {len(results)} results:")
    for i, result in enumerate(results[:3], 1):
        logger.info(f"\n   {i}. Similarity: {result['similarity']:.3f}")
        logger.info(f"      Query: {result['query']}")
        logger.info(f"      API: {result['api']}")
        logger.info(f"      Slots: {result.get('slots', {})}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Search test complete!")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_search())
