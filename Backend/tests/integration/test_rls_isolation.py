"""
RLS tenant-isolation integration tests.

Unit tests can prove the SQL is SHAPED correctly. Only a real PostgreSQL with
the Phase 3 migration applied can prove tenant isolation is actually ENFORCED —
and the failure mode here is silence, not an exception, so this test is the only
thing standing between "RLS is configured" and "RLS works".

Run:
    pytest tests/integration/test_rls_isolation.py -m integration

Requires:
    DATABASE_URL pointing at a PostgreSQL with `vector` installed and
    alembic upgrade head applied.

CI skips these (`-m "not integration"`). They belong in a pre-deploy gate.
"""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import text

from app.core.postgres import AsyncSessionLocal
from app.core.tenancy import current_tenant, tenant_session, verify_rls_enforced
from app.services.pgvector_store import PgVectorStore

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("DATABASE_URL", "").startswith("postgresql"),
        reason="RLS enforcement requires a real PostgreSQL",
    ),
]

DIM = 384


def _vec(seed: float) -> list[float]:
    return [seed] * DIM


@pytest.mark.asyncio
async def test_rls_is_enabled_and_forced():
    """
    ENABLE alone is silently ignored for the table OWNER — and apps usually
    connect as the owner. FORCE is what actually binds it.

    If this fails, every other test in this file would pass for the wrong reason.
    """
    async with AsyncSessionLocal() as session:
        for table in ("templates", "datasets", "vector_rows"):
            assert await verify_rls_enforced(session, table), (
                f"RLS not ENABLED+FORCED on {table}; tenant isolation is not in effect"
            )


@pytest.mark.asyncio
async def test_tenant_cannot_read_another_tenants_vectors():
    """The core guarantee: a query with no u_id predicate still sees only its own rows."""
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    store = PgVectorStore()

    async with tenant_session(tenant_a) as db:
        await _ensure_user(db, tenant_a)
        await store.upsert_rows(
            db,
            [{"query": "tenant A secret utterance", "api_name": "A_Api"}],
            [_vec(0.1)],
            embedding_model="test-model",
            dimension=DIM,
        )

    async with tenant_session(tenant_b) as db:
        await _ensure_user(db, tenant_b)
        await store.upsert_rows(
            db,
            [{"query": "tenant B secret utterance", "api_name": "B_Api"}],
            [_vec(0.1)],
            embedding_model="test-model",
            dimension=DIM,
        )

    # Identical query vector: without RLS, B's row would rank identically to A's.
    async with tenant_session(tenant_a) as db:
        result = await store.search(
            db, _vec(0.1), embedding_model="test-model", dimension=DIM, top_k=50
        )
        names = {r["api_name"] for r in result.rows}
        assert "A_Api" in names
        assert "B_Api" not in names, "CROSS-TENANT LEAK: tenant A read tenant B's vectors"


@pytest.mark.asyncio
async def test_session_without_tenant_sees_nothing():
    """
    Policies use current_setting('app.tenant_id', TRUE) so an unbound session
    yields NULL and matches no rows. Fail closed, never open.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            assert await current_tenant(session) is None
            count = (
                await session.execute(text("SELECT count(*) FROM vector_rows"))
            ).scalar()
            assert count == 0, "unbound session must see zero rows, not all rows"


@pytest.mark.asyncio
async def test_tenant_context_does_not_leak_across_pooled_connections():
    """
    THE LANDMINE. With `SET` instead of `SET LOCAL`, the GUC survives on the
    physical connection and the next checkout inherits it.

    Exhausting the pool makes reuse near-certain.
    """
    tenant = uuid.uuid4()
    async with tenant_session(tenant) as db:
        assert await current_tenant(db) == str(tenant)

    # pool_size=5, max_overflow=10 -> 16 checkouts guarantees reuse.
    for _ in range(16):
        async with AsyncSessionLocal() as session:
            async with session.begin():
                leaked = await current_tenant(session)
                assert leaked is None, (
                    f"TENANT LEAKED across pooled connection: {leaked}. "
                    f"apply_tenant_context must use set_config(..., is_local => true)."
                )


@pytest.mark.asyncio
async def test_write_into_another_tenant_is_rejected():
    """RLS WITH CHECK must block a forged u_id, not merely hide it on read."""
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()

    async with tenant_session(tenant_a) as db:
        await _ensure_user(db, tenant_a)
        with pytest.raises(Exception):
            await db.execute(
                text(
                    "INSERT INTO vector_rows "
                    "(u_id, query, embedding_model, dimension, embedding) "
                    "VALUES (CAST(:other AS uuid), 'forged', 'm', :d, CAST(:v AS vector))"
                ),
                {"other": str(tenant_b), "d": DIM, "v": "[" + ",".join(["0.1"] * DIM) + "]"},
            )


@pytest.mark.asyncio
async def test_hnsw_recall_survives_rls_filtering():
    """
    The subtle one. HNSW returns ef_search candidates and RLS filters them
    AFTERWARDS, so a tenant owning a small slice can get ZERO results back.

    One tenant with 5 rows among 500 belonging to others must still retrieve all
    5 — that only holds with hnsw.iterative_scan enabled.
    """
    minority = uuid.uuid4()
    store = PgVectorStore()

    for _ in range(20):
        noisy = uuid.uuid4()
        async with tenant_session(noisy) as db:
            await _ensure_user(db, noisy)
            await store.upsert_rows(
                db,
                [{"query": f"noise {i}", "api_name": "Noise"} for i in range(25)],
                [_vec(0.5 + i * 0.001) for i in range(25)],
                embedding_model="test-model",
                dimension=DIM,
            )

    async with tenant_session(minority) as db:
        await _ensure_user(db, minority)
        await store.upsert_rows(
            db,
            [{"query": f"mine {i}", "api_name": "Mine"} for i in range(5)],
            [_vec(0.9) for _ in range(5)],
            embedding_model="test-model",
            dimension=DIM,
        )

    async with tenant_session(minority) as db:
        result = await store.search(
            db, _vec(0.5), embedding_model="test-model", dimension=DIM, top_k=50
        )
        assert len(result.rows) == 5, (
            f"expected all 5 owned rows, got {len(result.rows)}. "
            f"RLS post-filtering collapsed HNSW recall — check hnsw.iterative_scan."
        )


async def _ensure_user(db, user_id: uuid.UUID) -> None:
    """Users are FK targets for vector_rows; insert bypassing RLS on users."""
    await db.execute(
        text(
            "INSERT INTO users (u_id, email, password_hash, created_at) "
            "VALUES (CAST(:u AS uuid), :e, 'x', now()) ON CONFLICT DO NOTHING"
        ),
        {"u": str(user_id), "e": f"{user_id}@test.local"},
    )
