"""
Tenant-Scoped Database Sessions
===============================

Enforces multi-tenant isolation at the STORAGE layer via PostgreSQL Row-Level
Security, replacing ~32 hand-written `u_id == user_id` filters scattered across
the routers.

WHY MOVE TENANCY INTO THE DATABASE
----------------------------------
v1 enforced isolation in application code: every query had to remember its own
`.where(Model.u_id == user_id)`. `datasets.py` alone contains 48 raw queries and
19 such filters. One forgotten filter is a silent cross-tenant data leak, and
nothing in the type system or the test suite catches it.

With RLS the database refuses to return another tenant's rows even if the query
forgets to ask. Application code becomes incapable of the mistake.

THREE LANDMINES THIS FILE EXISTS TO DEFUSE
------------------------------------------

1. `SET` LEAKS ACROSS POOLED CONNECTIONS.

   postgres.py builds an async engine with a connection pool (pool_size=5,
   max_overflow=10). A plain `SET app.tenant_id = ...` persists on the physical
   connection after the request finishes. The next request -- for a DIFFERENT
   tenant -- checks out that same connection and inherits the previous tenant's
   identity. The feature meant to prevent a cross-tenant leak becomes the cause
   of one.

   The setting must therefore be TRANSACTION-scoped, and every tenant query must
   run inside that transaction.

2. `SET LOCAL` CANNOT BE PARAMETERISED.

   PostgreSQL does not accept bind parameters in `SET LOCAL app.tenant_id = $1`.
   The obvious workaround -- f-stringing the UUID into the SQL -- is a SQL
   injection vector the moment the value is anything but a validated UUID.

   `set_config(setting, value, is_local => true)` is an ordinary function call,
   so it accepts bind parameters and is exactly equivalent to SET LOCAL. That is
   what this module uses.

3. RLS DOES NOT APPLY TO THE TABLE OWNER.

   `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` is silently ignored for the role
   that owns the table -- and applications typically connect as the owner. You
   get a green migration, passing tests, and zero actual enforcement.

   `FORCE ROW LEVEL SECURITY` is required as well. The migration applies it; see
   `verify_rls_enforced()` below for the runtime assertion.

BONUS: HNSW + RLS RECALL COLLAPSE
---------------------------------
pgvector's HNSW scan returns `ef_search` candidates and the RLS predicate filters
them AFTERWARDS. A tenant owning 2% of rows can therefore get ZERO results back
from a top-50 search -- no error, just silence.

`hnsw.iterative_scan = relaxed_order` (pgvector >= 0.8) makes the scan keep
pulling batches until it has enough rows that survive filtering. It is set on the
same transaction as the tenant id, since it must be scoped identically.
"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.postgres import AsyncSessionLocal

# GUC name referenced by every RLS policy. Must match the migration.
TENANT_GUC = "app.tenant_id"

# pgvector >= 0.8. 'relaxed_order' keeps scanning until enough post-filter rows
# are found; 'strict_order' is slower and rarely needed for top-k routing.
HNSW_ITERATIVE_SCAN = os.getenv("HNSW_ITERATIVE_SCAN", "relaxed_order")
# Ceiling on the iterative scan so a pathological filter cannot walk the table.
HNSW_MAX_SCAN_TUPLES = int(os.getenv("HNSW_MAX_SCAN_TUPLES", "20000"))
HNSW_EF_SEARCH = int(os.getenv("HNSW_EF_SEARCH", "100"))


class TenantContextError(RuntimeError):
    """Raised when a tenant-scoped operation is attempted without a tenant."""


async def apply_tenant_context(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    tune_hnsw: bool = True,
) -> None:
    """
    Bind `tenant_id` to the CURRENT TRANSACTION on `session`.

    Must be called inside an open transaction. The settings vanish on commit or
    rollback, which is precisely what keeps them from leaking onto the next
    checkout of this pooled connection.
    """
    if not isinstance(tenant_id, uuid.UUID):
        # Defence in depth: set_config takes a bind param so injection is not
        # possible, but a non-UUID here means a caller bug worth failing loudly.
        raise TenantContextError(f"tenant_id must be a UUID, got {type(tenant_id).__name__}")

    # is_local => true is exactly SET LOCAL, but accepts bind parameters.
    await session.execute(
        text("SELECT set_config(:guc, :val, true)"),
        {"guc": TENANT_GUC, "val": str(tenant_id)},
    )

    if tune_hnsw:
        # SET LOCAL genuinely cannot be parameterised, so these are interpolated.
        # Both values are read from env and coerced/validated below, never from
        # user input.
        mode = HNSW_ITERATIVE_SCAN
        if mode not in ("off", "strict_order", "relaxed_order"):
            logger.warning(f"Invalid HNSW_ITERATIVE_SCAN={mode!r}; falling back to relaxed_order")
            mode = "relaxed_order"
        try:
            await session.execute(text(f"SET LOCAL hnsw.iterative_scan = {mode}"))
            await session.execute(
                text(f"SET LOCAL hnsw.max_scan_tuples = {int(HNSW_MAX_SCAN_TUPLES)}")
            )
            await session.execute(text(f"SET LOCAL hnsw.ef_search = {int(HNSW_EF_SEARCH)}"))
        except Exception as exc:  # noqa: BLE001
            # Older pgvector, or a non-Postgres backend under test. Vector search
            # still works; recall under RLS filtering is simply not protected.
            logger.debug(f"HNSW session tuning unavailable ({exc})")


@asynccontextmanager
async def tenant_session(tenant_id: uuid.UUID) -> AsyncIterator[AsyncSession]:
    """
    Open a session whose transaction is bound to `tenant_id` for its whole life.

    Use directly in Celery tasks and scripts, where there is no request to hang a
    FastAPI dependency off:

        async with tenant_session(user_id) as db:
            rows = await db.execute(select(Dataset))   # no u_id filter needed
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():          # explicit transaction: SET LOCAL needs one
            await apply_tenant_context(session, tenant_id)
            yield session
            # commit on clean exit / rollback on exception, both drop the GUC


async def verify_rls_enforced(session: AsyncSession, table: str = "templates") -> bool:
    """
    Assert at startup that RLS is not merely enabled but FORCED.

    `relrowsecurity` alone is the trap: it reads as enabled while doing nothing
    for the owning role. `relforcerowsecurity` is the flag that actually binds
    the owner. Call this during startup and fail loudly rather than shipping
    tenancy that silently does not apply.
    """
    try:
        row = (
            await session.execute(
                text(
                    "SELECT relrowsecurity, relforcerowsecurity "
                    "FROM pg_class WHERE relname = :t"
                ),
                {"t": table},
            )
        ).first()
    except Exception as exc:  # noqa: BLE001 - non-Postgres backends (CI/SQLite)
        logger.debug(f"RLS verification skipped ({exc})")
        return False

    if row is None:
        logger.error(f"RLS verification: table '{table}' not found")
        return False

    enabled, forced = bool(row[0]), bool(row[1])
    if enabled and forced:
        logger.info(f"RLS verified on '{table}': enabled and FORCED")
        return True
    if enabled and not forced:
        logger.error(
            f"RLS on '{table}' is ENABLED but NOT FORCED. The application role "
            f"likely owns this table, so policies are being bypassed and tenant "
            f"isolation is NOT in effect. Run: "
            f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;"
        )
    else:
        logger.error(f"RLS is NOT enabled on '{table}'; tenant isolation is not in effect")
    return False


async def current_tenant(session: AsyncSession) -> Optional[str]:
    """Read back the tenant bound to this transaction. Diagnostics and tests."""
    try:
        val = (
            await session.execute(
                text("SELECT current_setting(:guc, true)"), {"guc": TENANT_GUC}
            )
        ).scalar()
        return val or None
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_tenant_db(current_user_dep: Any):
    """
    Build a tenant-scoped `get_db` replacement bound to an auth dependency.

    Wire it once in the router module:

        from app.api.v1.auth import get_current_user
        tenant_db = get_tenant_db(get_current_user)

        @router.get("/datasets")
        async def list_datasets(db: AsyncSession = Depends(tenant_db)):
            # RLS restricts this to the caller's rows automatically
            return (await db.execute(select(Dataset))).scalars().all()

    The whole request runs in one transaction so the GUC stays in scope. That is
    a deliberate trade: it is what makes tenancy safe under connection pooling.
    """
    from fastapi import Depends

    async def _dependency(user: Any = Depends(current_user_dep)) -> AsyncIterator[AsyncSession]:
        tenant_id = getattr(user, "u_id", None) or getattr(user, "id", None)
        if tenant_id is None:
            raise TenantContextError("authenticated user carries no tenant id")
        if not isinstance(tenant_id, uuid.UUID):
            tenant_id = uuid.UUID(str(tenant_id))

        async with AsyncSessionLocal() as session:
            async with session.begin():
                await apply_tenant_context(session, tenant_id)
                yield session

    return _dependency
