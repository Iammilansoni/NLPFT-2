"""Database configuration and connection for NLPForge."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from app.core.config import settings
from app.core.logger import logger


class DatabaseManager:
    """MongoDB database manager."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """Connect to MongoDB."""
        try:
            logger.info(f"🔌 Connecting to MongoDB at {settings.mongodb_url}")
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.mongodb_database]
            
            # Test the connection
            await self.client.admin.command('ping')
            logger.info("✅ Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            logger.info("🔌 Disconnecting from MongoDB")
            self.client.close()
            self.client = None
            self.database = None
            logger.info("✅ Disconnected from MongoDB")
    
    async def ping(self) -> bool:
        """Ping the database to check connection."""
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        if not self.database:
            raise RuntimeError("Database not connected")
        return self.database[collection_name]


# Global database manager instance
db_manager = DatabaseManager()

# Convenience property to access the database
@property
def db() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    if not db_manager.database:
        raise RuntimeError("Database not connected")
    return db_manager.database

# Make db accessible as a module attribute
class DatabaseProxy:
    """Proxy to access the database."""
    
    def __getattr__(self, name):
        if not db_manager.database:
            raise RuntimeError("Database not connected")
        return getattr(db_manager.database, name)
    
    async def command(self, command):
        """Execute a database command."""
        if not db_manager.database:
            raise RuntimeError("Database not connected")
        return await db_manager.database.command(command)

db = DatabaseProxy()