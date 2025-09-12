"""Database configuration and connection for NLPForge."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore
from typing import Optional, Any, Dict
from pymongo.collection import Collection  # type: ignore

from app.core.config import settings
from app.core.logger import logger


class DatabaseManager:
    """MongoDB database manager."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None  # type: ignore
        self.database: Optional[AsyncIOMotorDatabase] = None  # type: ignore
    
    async def connect(self) -> None:
        """Connect to MongoDB."""
        try:
            logger.info(f"🔌 Connecting to MongoDB at {settings.mongodb_url}")
            self.client = AsyncIOMotorClient(settings.mongodb_url)  # type: ignore
            if self.client is not None:  # type: ignore
                self.database = self.client[settings.mongodb_database]  # type: ignore
                
                # Test the connection with timeout
                await asyncio.wait_for(
                    self.client.admin.command('ping'),  # type: ignore
                    timeout=5.0
                )
                logger.info("✅ Successfully connected to MongoDB")
            
        except asyncio.TimeoutError:
            logger.warning("⚠️  MongoDB connection timeout - running without database")
            self.client = None
            self.database = None
        except Exception as e:
            logger.warning(f"⚠️  Failed to connect to MongoDB: {e} - running without database")
            self.client = None
            self.database = None
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client is not None:  # type: ignore
            logger.info("🔌 Disconnecting from MongoDB")
            self.client.close()  # type: ignore
            self.client = None
            self.database = None
            logger.info("✅ Disconnected from MongoDB")
    
    async def ping(self) -> bool:
        """Ping the database to check connection."""
        try:
            if self.client is not None:  # type: ignore
                await self.client.admin.command('ping')  # type: ignore
                return True
            return False
        except Exception:
            return False
    
    def get_collection(self, collection_name: str) -> Any:  # type: ignore
        """Get a collection from the database."""
        if self.database is None:  # type: ignore
            raise RuntimeError("Database not connected")
        return self.database[collection_name]  # type: ignore


# Global database manager instance
db_manager = DatabaseManager()


class DatabaseProxy:
    """Proxy to access the database."""
    
    def __getattr__(self, name: str) -> Any:
        if db_manager.database is None:  # type: ignore
            raise RuntimeError("Database not connected")
        return getattr(db_manager.database, name)  # type: ignore
    
    async def command(self, command: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
        """Execute a database command."""
        if db_manager.database is None:  # type: ignore
            raise RuntimeError("Database not connected")
        return await db_manager.database.command(command)  # type: ignore


# Database proxy instance
db = DatabaseProxy()