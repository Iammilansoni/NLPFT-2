"""
Bootstrap script: grant (or revoke) the admin role for a user.

This is the ONLY way to create the first administrator - the API
intentionally provides no self-service path to admin privileges.

Usage (from the Backend directory):
    python scripts/make_admin.py user@example.com
    python scripts/make_admin.py user@example.com --revoke
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Allow running as `python scripts/make_admin.py` from the Backend dir
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, update  # noqa: E402

from app.core.postgres import AsyncSessionLocal  # noqa: E402
from app.models.database_models import User  # noqa: E402


async def set_admin(email: str, value: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            print(f"ERROR: no user found with email: {email}")
            return 1

        await session.execute(
            update(User).where(User.u_id == user.u_id).values(is_admin=value)
        )
        await session.commit()

        action = "granted to" if value else "revoked from"
        print(f"OK: admin role {action} {email} (u_id={user.u_id})")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Grant or revoke the admin role.")
    parser.add_argument("email", help="Email address of the user")
    parser.add_argument("--revoke", action="store_true", help="Revoke instead of grant")
    args = parser.parse_args()
    return asyncio.run(set_admin(args.email, 0 if args.revoke else 1))


if __name__ == "__main__":
    raise SystemExit(main())
