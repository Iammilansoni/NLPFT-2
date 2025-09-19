# app/core/database.py
"""Database configuration and connection for NLPForge."""

from __future__ import annotations

import asyncio
from typing import Optional, Any, Dict, TYPE_CHECKING

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from fastapi import HTTPException

from app.core.config import settings
from app.core.logger import logger

if TYPE_CHECKING:
    # only for static type checking (avoid circular imports at runtime)
    from app.core.dictionary_repository import DictionaryRepository
    from app.services.dictionary_service import DictionaryService
    from app.nlp.enhanced_rule_engine import EnhancedRuleEngine


class DatabaseManager:
    """MongoDB database manager with dictionary integration."""

    def __init__(self) -> None:
        self.client: Optional[AsyncIOMotorClient[Any]] = None
        self.database: Optional[AsyncIOMotorDatabase[Dict[str, Any]]] = None
        self.db: Optional[AsyncIOMotorDatabase[Dict[str, Any]]] = None  # backwards compatibility alias

        # Dictionary components (forward-referenced types)
        self.dictionary_repository: Optional["DictionaryRepository"] = None
        self.dictionary_service: Optional["DictionaryService"] = None
        self.rule_engine: Optional["EnhancedRuleEngine"] = None

    async def connect(self) -> None:
        """Connect to MongoDB and initialize dictionary services."""
        try:
            logger.info(f"🔌 Connecting to MongoDB at {settings.mongodb_url}")
            self.client = AsyncIOMotorClient(settings.mongodb_url)

            self.database = self.client[settings.mongodb_database]
            self.db = self.database  # compatibility alias

            # Test the connection with timeout
            await asyncio.wait_for(self.client.admin.command("ping"), timeout=5.0)
            logger.info("✅ Successfully connected to MongoDB")

            # Initialize dictionary services (imports inside to avoid circular imports)
            await self._initialize_dictionary_services()

        except asyncio.TimeoutError:
            logger.warning("⚠️  MongoDB connection timeout - running without database")
            self._clear_connection_state()
        except Exception as e:
            logger.warning(f"⚠️  Failed to connect to MongoDB: {e} - running without database")
            self._clear_connection_state()

    def _clear_connection_state(self) -> None:
        self.client = None
        self.database = None
        self.db = None
        # clear services as well
        self.dictionary_repository = None
        self.dictionary_service = None
        self.rule_engine = None

    async def _initialize_dictionary_services(self) -> None:
        """Initialize dictionary repository, service, and rule engine."""
        try:
            if self.database is None:
                logger.info("No database available; skipping dictionary service initialization")
                return

            # Runtime imports here prevent circular import problems
            from app.core.dictionary_repository import DictionaryRepository
            from app.services.dictionary_service import DictionaryService
            from app.nlp.enhanced_rule_engine import EnhancedRuleEngine

            # Initialize repository
            self.dictionary_repository = DictionaryRepository(self.database)
            await self.dictionary_repository.create_indexes()

            # Initialize service
            self.dictionary_service = DictionaryService(self.dictionary_repository)

            # Initialize Enhanced Rule Engine 
            self.rule_engine = EnhancedRuleEngine(self.dictionary_repository)
            logger.info("Enhanced Rule Engine initialized with MongoDB repository")

            # Register hot-reload callback if the service supports it
            if hasattr(self.dictionary_service, "register_hot_reload_callback"):
                # Create wrapper callback for Enhanced Rule Engine
                async def rule_engine_reload_wrapper() -> None:
                    """Wrapper for Enhanced Rule Engine reload compatibility."""
                    try:
                        # Enhanced Rule Engine doesn't need async reload - it loads on demand
                        logger.info("Enhanced Rule Engine hot-reload callback triggered")
                    except Exception as e:
                        logger.error(f"Enhanced Rule Engine reload wrapper failed: {e}")
                
                # type: ignore[arg-type]  # runtime callback registration; static checker already sees type via TYPE_CHECKING
                self.dictionary_service.register_hot_reload_callback(rule_engine_reload_wrapper)

            logger.info("✅ Dictionary services initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize dictionary services: {e}")
            # ensure a clean failure state
            self.dictionary_repository = None
            self.dictionary_service = None
            self.rule_engine = None

    async def disconnect(self) -> None:
        """Disconnect from MongoDB and clear services."""
        if self.client is not None:
            logger.info("🔌 Disconnecting from MongoDB")
            try:
                self.client.close()
            except Exception:
                # some motor clients don't raise here; suppress
                pass

        self._clear_connection_state()
        logger.info("✅ Disconnected from MongoDB")

    async def ping(self) -> bool:
        """Ping the database to check connection."""
        if self.client is None:
            return False
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection[Dict[str, Any]]:
        """Get a collection from the database."""
        if self.database is None:
            raise RuntimeError("Database not connected")
        return self.database[collection_name]

# Global database manager instance
db_manager = DatabaseManager()


# Dependency injection functions (used by FastAPI)
async def get_dictionary_service() -> "DictionaryService":
    """Get dictionary service instance for dependency injection."""
    if db_manager.dictionary_service is None:
        raise HTTPException(status_code=503, detail="Dictionary service not available")
    return db_manager.dictionary_service


async def get_dictionary_repository() -> "DictionaryRepository":
    """Get dictionary repository instance for dependency injection."""
    if db_manager.dictionary_repository is None:
        raise HTTPException(status_code=503, detail="Dictionary repository not available")
    return db_manager.dictionary_repository


async def get_rule_engine() -> "EnhancedRuleEngine":
    """Get rule engine instance for dependency injection."""
    if db_manager.rule_engine is None:
        raise HTTPException(status_code=503, detail="Rule engine not available")
    return db_manager.rule_engine


class DatabaseProxy:
    """Proxy to access the database object (thin wrapper)."""

    def __getattr__(self, name: str) -> Any:
        if db_manager.database is None:
            raise RuntimeError("Database not connected")
        return getattr(db_manager.database, name)

    async def command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a database command."""
        if db_manager.database is None:
            raise RuntimeError("Database not connected")
        return await db_manager.database.command(command)


# Database proxy instance
db = DatabaseProxy()
