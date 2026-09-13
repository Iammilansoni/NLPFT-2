#!/usr/bin/env python
"""
Idempotent migration runner for container boot.

WHY THIS EXISTS
---------------
The container boots via `init_db_direct.py`, which creates every table that
has a SQLAlchemy model via `Base.metadata.create_all()`. That covers the app's
ORM-mapped tables but NOT objects that only exist in a raw Alembic migration --
concretely, `vector_rows` and the RLS policies added in
alembic/versions/20260823_pgvector_and_rls.py. Nothing ever ran
`alembic upgrade head` in any deployment of this stack, so that migration had
never actually applied anywhere: Stage 1 pgvector recall had no table to read
from, and the RLS tenant isolation the README describes was never turned on.

create_all() also means `alembic_version` starts empty even though the schema
already matches every migration up to (but not including) the pgvector/RLS
one. A plain `alembic upgrade head` from an empty version table would replay
the entire history from `001` -- including `CREATE TABLE users`, which
create_all() already did -- and fail on the first statement. So: stamp the
baseline that create_all() already covers, once, then upgrade to head. On
every later boot alembic_version is already set and `upgrade head` is a no-op.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import settings  # noqa: E402

# The last revision whose end-state create_all() already produces from the
# current models. Everything after this point (currently just the pgvector +
# RLS migration) exists ONLY as a migration, never as an ORM model.
BASELINE_REVISION = "20260612_add_is_admin"


def _sync_url() -> str:
    # alembic/env.py and the app both use an async driver; DDL introspection
    # here just needs a plain sync connection.
    url = settings.database_url
    return url.replace("postgresql+asyncpg://", "postgresql://")


def _current_alembic_version(sync_url: str) -> str | None:
    engine = create_engine(sync_url)
    try:
        with engine.connect() as conn:
            has_table = conn.execute(
                text("SELECT to_regclass('public.alembic_version')")
            ).scalar()
            if not has_table:
                return None
            return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    finally:
        engine.dispose()


def main() -> int:
    current = _current_alembic_version(_sync_url())

    if current is None:
        print(f"[migrations] no alembic version recorded — stamping baseline {BASELINE_REVISION}")
        subprocess.run(
            [sys.executable, "-m", "alembic", "stamp", BASELINE_REVISION],
            check=True,
            cwd=BACKEND_ROOT,
        )
    else:
        print(f"[migrations] current revision: {current}")

    print("[migrations] running alembic upgrade head")
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=BACKEND_ROOT,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
