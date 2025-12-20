"""
Initialize PostgreSQL Database
Run this script to create all tables
"""

import asyncio
from app.core.postgres import init_db
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
