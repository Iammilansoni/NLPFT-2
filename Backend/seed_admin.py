"""
Database seed script — creates a default admin user if the users table is empty.

Runs automatically after init_db_direct.py on every container startup.
Safe to run multiple times (idempotent — skips if any user already exists).

Credentials are read from environment variables:
    SEED_ADMIN_EMAIL       (default: admin@nlpforge.dev)
    SEED_ADMIN_PASSWORD    (REQUIRED outside local mode - see below)
    SEED_ADMIN_USERNAME    (default: admin)

SECURITY
--------
This creates a PRE-VERIFIED admin account and runs on every container boot.
The convenience default password is therefore restricted to local development:
outside EXECUTION_MODE=local, seeding aborts unless SEED_ADMIN_PASSWORD is set
explicitly.

Without that guard, a public repository publishes the credentials to every
deployment built from it - which is the same "default credentials" class of
issue fixed in the day-1 hardening pass. A default that is safe on localhost is
not safe once the same image is deployed.
"""
import asyncio
import os
import re
import sys
import uuid
from datetime import datetime, timezone


def get_clean_db_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    return url.strip().replace("\r", "")


async def main():
    db_url = get_clean_db_url()
    if not db_url:
        print("SEED: DATABASE_URL not set — skipping admin seed.", file=sys.stderr)
        return

    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@nlpforge.dev")
    admin_username = os.getenv("SEED_ADMIN_USERNAME", "admin")

    # The default password is a localhost-only convenience. Anywhere else, an
    # unset SEED_ADMIN_PASSWORD means a publicly-known admin credential on a
    # reachable host, so refuse to seed rather than create one.
    admin_password = os.getenv("SEED_ADMIN_PASSWORD")
    execution_mode = os.getenv("EXECUTION_MODE", "local").lower()

    if not admin_password:
        if execution_mode != "local":
            print(
                "SEED: refusing to seed an admin account.\n"
                f"      EXECUTION_MODE={execution_mode!r} (not 'local') and "
                "SEED_ADMIN_PASSWORD is unset.\n"
                "      Set SEED_ADMIN_PASSWORD to a strong secret, e.g.\n"
                "        fly secrets set SEED_ADMIN_PASSWORD=\"$(openssl rand -base64 24)\"",
                file=sys.stderr,
            )
            sys.exit(1)
        admin_password = "Admin@12345"
        print(
            "SEED: using the default local development password. "
            "Never expose this instance publicly.",
            file=sys.stderr,
        )

    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import select, func

        from app.models.database_models import User
        from app.services.auth_service import AuthService

        engine = create_async_engine(db_url, echo=False, pool_pre_ping=True,
                                     connect_args={"timeout": 15})
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Check if ANY user already exists
            result = await session.execute(select(func.count(User.u_id)))
            user_count = result.scalar_one()

            if user_count > 0:
                print(f"SEED: {user_count} user(s) already exist — skipping seed.")
                await engine.dispose()
                return

            # Create the admin user
            hashed = AuthService.hash_password(admin_password)
            admin = User(
                u_id=uuid.uuid4(),
                email=admin_email,
                password=hashed,
                user_name=admin_username,
                email_verified=True,   # Pre-verified — no SMTP required
                is_expert=True,        # Full platform access
                is_admin=True,         # Administrator privileges
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            session.add(admin)
            await session.commit()

            print("=" * 55)
            print("SEED: Default admin user created")
            print("=" * 55)
            print(f"  Email:    {admin_email}")
            print(f"  Password: {'*' * (len(admin_password) - 4) + admin_password[-4:]}")
            print(f"  Username: {admin_username}")
            print(f"  Role:     admin + expert")
            print(f"  Verified: yes")
            print("=" * 55)

        await engine.dispose()

    except Exception as e:
        print(f"SEED: Error creating admin user: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        # Don't block startup — the app runs fine without a seed user
        print("SEED: Continuing startup.", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
