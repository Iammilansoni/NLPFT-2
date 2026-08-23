"""
Phase 3 unit tests — tenancy, pgvector store, repositories.

These target the three landmines specifically, because each one FAILS SILENTLY
in production and passes a naive test suite:

  * `SET` instead of `SET LOCAL`      -> tenant leaks across pooled connections
  * f-stringed tenant id              -> SQL injection
  * an application-level u_id filter  -> masks a broken RLS config

Policy enforcement itself needs a real PostgreSQL and lives in
tests/integration/test_rls_isolation.py.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Tuple

import numpy as np
import pytest

from app.core.tenancy import (
    TENANT_GUC,
    TenantContextError,
    apply_tenant_context,
)
from app.services.pgvector_store import PgVectorStore, to_pgvector


# ===========================================================================
# Fakes
# ===========================================================================

class _RecordingSession:
    """Captures executed statements without needing a database."""

    def __init__(self, rows: List[Dict[str, Any]] | None = None) -> None:
        self.statements: List[Tuple[str, Any]] = []
        self._rows = rows or []

    async def execute(self, stmt: Any, params: Any = None):
        self.statements.append((str(stmt), params))
        return _FakeResult(self._rows)

    @property
    def sql(self) -> str:
        return "\n".join(s for s, _ in self.statements)


class _FakeResult:
    def __init__(self, rows: List[Dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self):
        return iter(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None

    def scalar(self):
        return self._rows[0] if self._rows else None

    @property
    def rowcount(self) -> int:
        return len(self._rows)


# ===========================================================================
# Tenancy — landmine 1 & 2
# ===========================================================================

@pytest.mark.asyncio
async def test_tenant_context_uses_transaction_local_set_config():
    """
    LANDMINE 1: a plain `SET` persists on the pooled connection and the next
    request — a different tenant — inherits it.

    The tenant id must be bound with set_config(..., is_local => true), which is
    transaction-scoped and evaporates on commit or rollback.
    """
    session = _RecordingSession()
    tenant = uuid.uuid4()

    await apply_tenant_context(session, tenant, tune_hnsw=False)

    sql = session.sql
    assert "set_config" in sql, "tenant id must be bound via set_config"
    assert "true" in sql, "set_config must pass is_local => true"

    # A bare `SET app.tenant_id` (without LOCAL) must never appear.
    assert not re.search(r"\bSET\s+app\.tenant_id\b", sql, re.IGNORECASE), (
        "session-scoped SET leaks the tenant across pooled connections"
    )


@pytest.mark.asyncio
async def test_tenant_id_is_bound_as_parameter_not_interpolated():
    """
    LANDMINE 2: SET LOCAL cannot take bind params, and f-stringing the value in
    is an injection vector. set_config takes parameters, so the UUID must appear
    in the params dict — never in the SQL text.
    """
    session = _RecordingSession()
    tenant = uuid.uuid4()

    await apply_tenant_context(session, tenant, tune_hnsw=False)

    stmt_sql, params = session.statements[0]
    assert str(tenant) not in stmt_sql, "tenant id was interpolated into SQL"
    assert params["val"] == str(tenant), "tenant id must travel as a bind parameter"
    assert params["guc"] == TENANT_GUC


@pytest.mark.asyncio
async def test_non_uuid_tenant_is_rejected():
    session = _RecordingSession()
    with pytest.raises(TenantContextError):
        await apply_tenant_context(session, "'; DROP TABLE users; --")  # type: ignore[arg-type]
    assert session.statements == [], "nothing should execute for an invalid tenant"


@pytest.mark.asyncio
async def test_hnsw_iterative_scan_is_set_on_the_same_transaction():
    """
    RLS post-filters HNSW results, so a tenant owning few rows can get ZERO
    results back from a top-k scan. iterative_scan must be enabled, and scoped to
    the same transaction as the tenant id.
    """
    session = _RecordingSession()
    await apply_tenant_context(session, uuid.uuid4(), tune_hnsw=True)

    sql = session.sql
    assert "hnsw.iterative_scan" in sql
    assert "relaxed_order" in sql
    assert "SET LOCAL" in sql, "HNSW tuning must be transaction-scoped too"


# ===========================================================================
# pgvector serialisation
# ===========================================================================

def test_to_pgvector_format():
    assert to_pgvector([1.0, 2.5, -0.25]) == "[1,2.5,-0.25]"
    assert to_pgvector(np.array([0.1, 0.2], dtype=np.float32)).startswith("[")


def test_to_pgvector_flattens_and_handles_numpy():
    out = to_pgvector(np.array([[1.0, 2.0]], dtype=np.float32))
    assert out == "[1,2]"


# ===========================================================================
# pgvector store — landmine 3
# ===========================================================================

@pytest.mark.asyncio
async def test_search_sql_contains_no_tenant_filter():
    """
    LANDMINE 3: adding a defensive `u_id = ...` here would mask a broken RLS
    configuration — the app would look correct while workers and scripts that
    bypass the router leaked data.

    Isolation is RLS's job. Its absence in this SQL is intentional.
    """
    session = _RecordingSession(rows=[])
    store = PgVectorStore()

    await store.search(
        session,
        query_vector=[0.1] * 384,
        embedding_model="bge-small",
        dimension=384,
        top_k=25,
    )

    sql = session.sql
    assert "u_id" not in sql, "tenant filtering must come from RLS, not the query"
    assert "current_setting" not in sql, "reads must not hand-roll the tenant either"


@pytest.mark.asyncio
async def test_search_filters_on_dimension_to_hit_the_partial_index():
    """
    HNSW indexes are partial (`WHERE dimension = N`). Without this predicate the
    planner falls back to a sequential scan and latency silently collapses.
    """
    session = _RecordingSession(rows=[])
    await PgVectorStore().search(
        session, [0.1] * 768, embedding_model="mpnet", dimension=768
    )
    sql = session.sql
    assert "dimension = :dim" in sql
    assert "vector(768)" in sql, "cast must match the partial index expression"
    assert "<=>" in sql, "must use the cosine distance operator"


@pytest.mark.asyncio
async def test_search_rejects_dimension_mismatch():
    """A 384-dim query against a 768-dim index is a bug, not a degraded result."""
    with pytest.raises(ValueError, match="dimension"):
        await PgVectorStore().search(
            _RecordingSession(), [0.1] * 384, embedding_model="m", dimension=768
        )


@pytest.mark.asyncio
async def test_search_maps_distance_to_similarity():
    """Stage 2 consumes `similarity`; pgvector emits cosine DISTANCE."""
    session = _RecordingSession(
        rows=[
            {
                "row_uid": uuid.uuid4(),
                "t_id": uuid.uuid4(),
                "dataset_id": None,
                "query": "log me in",
                "api_name": "User_Login",
                "endpoint": "/auth/login",
                "method": "POST",
                "scenario_type": "valid",
                "test_category": None,
                "intent_type": "action",
                "notes": None,
                "embedding_model": "bge-small",
                "distance": 0.25,
            }
        ]
    )
    result = await PgVectorStore().search(
        session, [0.1] * 384, embedding_model="bge-small", dimension=384
    )
    row = result.rows[0]
    assert row["similarity"] == pytest.approx(0.75)
    assert row["vector_score"] == pytest.approx(0.25)
    # Field names must match what the cross-encoder aggregator expects.
    assert {"t_id", "template_id", "query", "api_name"} <= set(row)


@pytest.mark.asyncio
async def test_upsert_derives_tenant_from_session_not_arguments():
    """
    Writes must take u_id from the transaction GUC. Accepting it as a parameter
    would let a caller write into another tenant, which RLS WITH CHECK would then
    have to catch — better not to offer the footgun at all.
    """
    session = _RecordingSession()
    store = PgVectorStore()

    rows = [{"t_id": uuid.uuid4(), "query": "hello", "api_name": "X"}]
    n = await store.upsert_rows(
        session, rows, [[0.1] * 384], embedding_model="bge-small", dimension=384
    )

    assert n == 1
    sql = session.sql
    assert "current_setting('app.tenant_id')::uuid" in sql
    _, params = session.statements[0]
    assert "u_id" not in params[0], "u_id must not be caller-supplied"


@pytest.mark.asyncio
async def test_upsert_rejects_wrong_dimension_vector():
    with pytest.raises(ValueError, match="dimension mismatch"):
        await PgVectorStore().upsert_rows(
            _RecordingSession(),
            [{"query": "x"}],
            [[0.1] * 128],
            embedding_model="bge-small",
            dimension=384,
        )


@pytest.mark.asyncio
async def test_upsert_rejects_length_mismatch():
    with pytest.raises(ValueError, match="length mismatch"):
        await PgVectorStore().upsert_rows(
            _RecordingSession(),
            [{"query": "a"}, {"query": "b"}],
            [[0.1] * 384],
            embedding_model="m",
            dimension=384,
        )


# ===========================================================================
# Repository
# ===========================================================================

def test_repository_defines_no_tenant_filter():
    """
    Guards against a well-meaning future edit re-adding `u_id ==` filters, which
    would hide RLS misconfiguration rather than protect against it.
    """
    import inspect

    from app.repositories.dataset_repository import DatasetRepository

    source = inspect.getsource(DatasetRepository)
    assert "u_id ==" not in source, (
        "tenancy belongs to RLS; an application-level filter masks a broken policy"
    )


def test_repository_rejects_invalid_embedding_status():
    import asyncio

    from app.repositories.dataset_repository import DatasetRepository

    repo = DatasetRepository(_RecordingSession())
    with pytest.raises(ValueError, match="invalid embedding_status"):
        asyncio.run(repo.set_embedding_status(uuid.uuid4(), "banana"))
