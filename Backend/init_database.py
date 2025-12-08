"""
Initialize PostgreSQL Database
Run this script to create all tables and sync templates from api_template.json
"""

import asyncio
import os
from pathlib import Path
from app.core.postgres import init_db
from app.services.template_service import get_template_service
from app.core.logger import logger


async def main():
    """Initialize database"""
    logger.info("=" * 60)
    logger.info("🚀 Initializing PostgreSQL Database")
    logger.info("=" * 60)
    
    # Create tables
    logger.info("\n📊 Creating database tables...")
    await init_db()
    logger.info("✅ Tables created successfully")
    
    # Sync templates from api_template.json
    logger.info("\n📋 Syncing API templates from api_template.json...")
    template_service = get_template_service()
    
    # Find api_template.json
    backend_dir = Path(__file__).parent
    json_path = backend_dir / "api_template.json"
    
    if not json_path.exists():
        logger.warning(f"⚠️  api_template.json not found at {json_path}")
        logger.info("Skipping template sync. You can run sync later via API.")
    else:
        try:
            stats = await template_service.sync_from_json(str(json_path))
            
            logger.info(f"\n✅ Template Sync Complete!")
            logger.info(f"   • Loaded:  {stats['loaded']} templates from JSON")
            logger.info(f"   • Created: {stats['created']} new templates")
            logger.info(f"   • Updated: {stats['updated']} existing templates")
            logger.info(f"   • Errors:  {stats['errors']} errors")
            
            # Load templates into memory
            await template_service.load_all_templates()
            cache_stats = template_service.get_cache_stats()
            
            logger.info(f"\n💾 Cached {cache_stats['total_templates']} templates in memory")
            logger.info(f"   • System templates:  {cache_stats['system_templates']}")
            logger.info(f"   • Custom templates:  {cache_stats['custom_templates']}")
            logger.info(f"\n   Available APIs: {', '.join(cache_stats['intents'])}")
            
        except Exception as e:
            logger.error(f"❌ Error syncing templates: {e}")
            raise
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Database Initialization Complete!")
    logger.info("=" * 60)
    logger.info("\n🧠 PostgreSQL is ready as your main brain")
    logger.info("⚡ Redis will handle embeddings and fast memory")
    logger.info("\n🎯 Next steps:")
    logger.info("   1. Start Redis: docker run -d -p 6379:6379 redis/redis-stack")
    logger.info("   2. Start API: python -m app.main")
    logger.info("   3. Test endpoint: http://localhost:8000/docs")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
