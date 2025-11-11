"""
PostgreSQL Database Configuration - Main Brain (Permanent Storage)
Stores: datasets, API metadata, query logs, user data
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, Boolean
from datetime import datetime
import os
from dotenv import load_dotenv
from app.core.logger import logger

load_dotenv()

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://nlpforge:nlpforge_secure_password@localhost:5432/nlpforge"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    connect_args={
        "timeout": 10,
        "command_timeout": 60,
        "server_settings": {
            "application_name": "nlpforge_backend"
        }
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class Dataset(Base):
    """
    Dataset model - stores information about generated datasets
    """
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    intent = Column(String(50), nullable=False, index=True)
    api_name = Column(String(100), nullable=False)
    endpoint = Column(String(255))
    method = Column(String(10))
    total_examples = Column(Integer, default=0)
    csv_path = Column(String(500))
    json_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON)  # Use metadata_ to avoid SQLAlchemy reserved keyword


class QueryLog(Base):
    """
    Query log model - stores all user queries and results
    """
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    intent = Column(String(50), index=True)
    slots = Column(JSON)
    confidence = Column(Float)
    best_match_api = Column(String(100))
    best_match_score = Column(Float)
    dataset_generated = Column(Boolean, default=False)
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(100), index=True)  # For future authentication
    session_id = Column(String(100), index=True)
    metadata_ = Column("metadata", JSON)  # Use metadata_ to avoid SQLAlchemy reserved keyword


class TestRun(Base):
    """
    Test run model - stores test execution results for dashboard
    """
    __tablename__ = "test_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    intent = Column(String(50), index=True)
    status = Column(String(20), nullable=False, index=True)  # 'passed', 'failed', 'running', 'pending'
    confidence = Column(Float)
    tests_count = Column(Integer, default=0)  # Number of tests executed
    processing_time_ms = Column(Float)
    best_match_api = Column(String(100))
    best_match_score = Column(Float)
    search_results_count = Column(Integer, default=0)
    dataset_generated = Column(Boolean, default=False)
    error_message = Column(Text)  # Error message if failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(String(100), index=True)  # For future authentication
    session_id = Column(String(100), index=True)
    metadata_ = Column("metadata", JSON)  # Use metadata_ to avoid SQLAlchemy reserved keyword


class APITemplate(Base):
    """
    API template model - stores custom API templates
    """
    __tablename__ = "api_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    intent = Column(String(50), unique=True, nullable=False, index=True)
    api_name = Column(String(100), nullable=False)
    description = Column(Text)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    fields = Column(JSON, nullable=False)  # List of required fields
    example_queries = Column(JSON)  # List of example queries
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_system = Column(Boolean, default=False)  # System vs user-defined
    metadata_ = Column("metadata", JSON)  # Use metadata_ to avoid SQLAlchemy reserved keyword


class EmbeddingMetadata(Base):
    """
    Embedding metadata model - tracks embeddings in Redis
    Links PostgreSQL permanent storage with Redis fast memory
    """
    __tablename__ = "embedding_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    redis_key = Column(String(100), unique=True, nullable=False, index=True)
    hash_id = Column(String(64), unique=True, nullable=False, index=True)
    query = Column(Text, nullable=False)
    intent = Column(String(50), nullable=False, index=True)
    dataset_id = Column(Integer, index=True)  # Foreign key to datasets
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON)  # Use metadata_ to avoid SQLAlchemy reserved keyword


class DatasetExample(Base):
    """
    Dataset example model - stores individual dataset examples
    Backup for Redis embeddings in permanent storage
    """
    __tablename__ = "dataset_examples"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False, index=True)
    query = Column(Text, nullable=False)
    intent = Column(String(50), nullable=False, index=True)
    slots = Column(JSON)
    api_name = Column(String(100))
    endpoint = Column(String(255))
    method = Column(String(10))
    hash_id = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_embedded = Column(Boolean, default=False)  # Tracks if in Redis
    metadata_ = Column("metadata", JSON)  # Use metadata_ to avoid SQLAlchemy reserved keyword


# Database session dependency
async def get_db():
    """
    FastAPI dependency to get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def close_db():
    """
    Close database connections
    """
    await engine.dispose()
    logger.info("PostgreSQL database connections closed")


# Database manager class
class DatabaseManager:
    """
    Manage PostgreSQL database operations
    """
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def connect(self):
        """Connect to database and create tables"""
        try:
            # Test connection first with a simple query
            from sqlalchemy import text
            async with self.session_factory() as session:
                await session.execute(text("SELECT 1"))
            
            # If connection works, initialize tables
            await init_db()
            logger.info("PostgreSQL: Main brain connected")
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
            logger.warning("Running without PostgreSQL - templates will be memory-only")
            # Don't raise - allow app to continue without PostgreSQL
    
    async def disconnect(self):
        """Close database connections"""
        await close_db()
        logger.info("PostgreSQL: Main brain disconnected")
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            from sqlalchemy import text
            async with self.session_factory() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()
