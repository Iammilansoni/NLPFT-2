"""PostgreSQL Database Configuration - Core Infrastructure"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv
from app.core.logger import logger

load_dotenv()

# Use DATABASE_URL from environment, fallback to individual components
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Build from individual components if DATABASE_URL not set
    pg_user = os.getenv("POSTGRES_USER", "nlpforge")
    pg_pass = os.getenv("POSTGRES_PASSWORD")
    if not pg_pass:
        logger.warning("POSTGRES_PASSWORD not set — database connection may fail")
        pg_pass = ""
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "nlpforge")
    DATABASE_URL = f"postgresql+asyncpg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

# SQLite (used in CI/testing) doesn't support PostgreSQL pool/connect args
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        connect_args={"timeout": 10, "command_timeout": 60, "server_settings": {"application_name": "nlpforge_enterprise"}},
    )

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass

async def get_db():
    """FastAPI dependency for database sessions"""
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
    """Initialize database - create all tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ PostgreSQL database initialized")
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise

async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("PostgreSQL connections closed")

class DatabaseManager:
    """Manage PostgreSQL database lifecycle"""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def connect(self):
        """Connect to database and create tables"""
        try:
            from sqlalchemy import text
            async with self.session_factory() as session:
                await session.execute(text("SELECT 1"))
            await init_db()
            logger.info("🧠 PostgreSQL connected - Enterprise schema ready")
        except Exception as e:
            logger.warning(f"⚠️  PostgreSQL connection failed: {e}")
    
    async def disconnect(self):
        """Close database connections"""
        await close_db()
    
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

db_manager = DatabaseManager()
