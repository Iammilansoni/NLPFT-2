"""
Database initialization script - creates all tables from SQLAlchemy models.
Runs automatically before uvicorn on every container startup.
Safe to run multiple times (idempotent - CREATE TABLE IF NOT EXISTS).
"""
import asyncio
import sys
import os
import re


def get_clean_db_url() -> str:
    """Get DATABASE_URL with any Windows CRLF artifacts stripped."""
    url = os.getenv("DATABASE_URL", "")
    # Strip any carriage returns that Windows env_file may inject
    url = url.strip().replace("\r", "")
    return url


def extract_password_from_url(url: str) -> str | None:
    """Extract password from a postgresql+asyncpg:// URL."""
    match = re.search(r"://[^:]+:([^@]+)@", url)
    return match.group(1) if match else None


async def main():
    print("=" * 55)
    print("NLPForge DB Initialization")
    print("=" * 55)

    db_url = get_clean_db_url()
    if not db_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)

    # Mask password for logging
    safe_url = re.sub(r":(.*?)@", ":****@", db_url)
    print(f"Target: {safe_url}")

    try:
        # Override the engine URL with the cleaned URL (no \r artifacts)
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.core.postgres import Base
        from app.models.database_models import (
            User, UserSettings, LLMProviderConfig, Template, Parameter,
            ExpectedResponse, Metadata, Dataset, CSVData, Model,
            EmbeddingModel, Embedding, AuditLog
        )

        # Import auxiliary models so their tables are registered with Base.metadata
        from app.models.email_verification_models import EmailVerification  # noqa
        from app.models.password_reset_models import PasswordReset  # noqa

        engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"timeout": 15},
        )

        print("Connecting...")
        async with engine.begin() as conn:
            print("Connected! Creating tables (if not exist)...")
            await conn.run_sync(Base.metadata.create_all)

        await engine.dispose()

        print("=" * 55)
        print("SUCCESS: Database schema ready!")
        print("=" * 55)
        tables = [t.name for t in Base.metadata.sorted_tables]
        print(f"Tables ({len(tables)}): {', '.join(tables)}")

    except Exception as e:
        print(f"\nERROR during DB initialization: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        print("\nContinuing startup — app will run in degraded mode.", file=sys.stderr)
        # Don't exit(1) — allow uvicorn to start even if DB init fails
        # The app handles missing DB gracefully


if __name__ == "__main__":
    asyncio.run(main())
