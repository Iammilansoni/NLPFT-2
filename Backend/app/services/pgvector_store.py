"""
pgvector Vector Store
=====================

Stage 1 recall backed by PostgreSQL + pgvector, replacing Redis HNSW as the
primary vector store.

WHY THE MIGRATION OFF REDIS
---------------------------
v1's Redis implementation was genuinely the best-engineered part of the codebase
-- per-model HNSW indexes with dimension guards, which most projects get wrong.
It is not being replaced because it was bad.

It is being replaced because tenancy cannot cross a storage boundary. Redis
enforced isolation with an application-supplied `TagField` filter on user_id: if
the caller forgets the filter, Redis happily returns everyone's vectors. Postgres
RLS refuses at the storage layer regardless of what the query asks for. Having
ONE tenancy model, enforced in one place, is worth more than a second datastore.

Secondary wins: one less service to run and pay for, vectors transactionally
consistent with the templates they reference (no more orphaned index entries),
and joins against relational data without a round trip.

The Redis path is retained behind VECTOR_BACKEND=redis so the two can be
benchmarked on the same eval harness rather than argued about.

INTERACTION WITH RLS -- THE IMPORTANT PART
------------------------------------------
An HNSW index scan returns `ef_search` candidates and RLS filters them
AFTERWARDS. For a tenant owning a small share of rows, a top-50 scan can return
ZERO surviving rows -- silently, with no error.

Every query here therefore runs on a session prepared by `app.core.tenancy`,
which sets `hnsw.iterative_scan = relaxed_order` on the same transaction. Callers
MUST use `tenant_session()` or the `get_tenant_db` dependency; a bare session
will both bypass tuning and (correctly) see no rows at all.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger

VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "pgvector").lower()


def to_pgvector(vec: Sequence[float]) -> str:
    """
    Render a vector in pgvector's text input format: '[0.1,0.2,...]'.

    Passed as a bind parameter and cast server-side, so this is not string
    interpolation into SQL.
    """
    arr = np.asarray(vec, dtype=np.float32).ravel()
    return "[" + ",".join(f"{float(x):.7g}" for x in arr) + "]"


@dataclass
class VectorSearchResult:
    rows: List[Dict[str, Any]]
    latency_ms: float
    backend: str = "pgvector"
    dimension: int = 0

    def __len__(self) -> int:
        return len(self.rows)


class PgVectorStore:
    """
    Vector storage and KNN retrieval over `vector_rows`.

    Every method takes an AsyncSession already bound to a tenant. This class does
    not know or care which tenant it is serving -- that is the point.
    """

    TABLE = "vector_rows"

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    async def upsert_rows(
        self,
        db: AsyncSession,
        rows: Sequence[Dict[str, Any]],
        embeddings: Sequence[Sequence[float]],
        embedding_model: str,
        dimension: int,
    ) -> int:
        """
        Insert indexed utterances with their vectors.

        `u_id` is deliberately NOT accepted as a parameter: it is filled from the
        transaction's tenant GUC, so a caller cannot write into another tenant
        even by mistake. The RLS WITH CHECK clause enforces the same thing a
        second time.
        """
        if not rows:
            return 0
        if len(rows) != len(embeddings):
            raise ValueError(
                f"rows/embeddings length mismatch: {len(rows)} vs {len(embeddings)}"
            )

        payload = []
        for row, vec in zip(rows, embeddings):
            arr = np.asarray(vec, dtype=np.float32).ravel()
            if arr.shape[0] != dimension:
                raise ValueError(
                    f"embedding dimension mismatch: expected {dimension}, got {arr.shape[0]}"
                )
            payload.append(
                {
                    "t_id": str(row["t_id"]) if row.get("t_id") else None,
                    "dataset_id": str(row["dataset_id"]) if row.get("dataset_id") else None,
                    "query": row.get("query", ""),
                    "api_name": row.get("api_name"),
                    "endpoint": row.get("endpoint"),
                    "method": row.get("method"),
                    "scenario_type": row.get("scenario_type", "valid"),
                    "test_category": row.get("test_category"),
                    "intent_type": row.get("intent_type"),
                    "notes": row.get("notes"),
                    "embedding_model": embedding_model,
                    "dimension": dimension,
                    "embedding": to_pgvector(arr),
                }
            )

        await db.execute(
            text(
                f"""
                INSERT INTO {self.TABLE}
                    (u_id, t_id, dataset_id, query, api_name, endpoint, method,
                     scenario_type, test_category, intent_type, notes,
                     embedding_model, dimension, embedding)
                VALUES
                    (current_setting('app.tenant_id')::uuid,
                     CAST(:t_id AS uuid), CAST(:dataset_id AS uuid), :query,
                     :api_name, :endpoint, :method, :scenario_type,
                     :test_category, :intent_type, :notes,
                     :embedding_model, :dimension, CAST(:embedding AS vector))
                """
            ),
            payload,
        )
        logger.info(
            f"pgvector: inserted {len(payload)} rows "
            f"(model={embedding_model}, dim={dimension})"
        )
        return len(payload)

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    async def search(
        self,
        db: AsyncSession,
        query_vector: Sequence[float],
        embedding_model: str,
        dimension: int,
        top_k: int = 25,
        dataset_id: Optional[uuid.UUID] = None,
        template_id: Optional[uuid.UUID] = None,
    ) -> VectorSearchResult:
        """
        KNN over the tenant's rows.

        Notes on the SQL:
          * `<=>` is pgvector's cosine DISTANCE operator; similarity is 1 - d,
            matching the convention the rest of the pipeline already uses.
          * The `dimension = :dim` predicate is not merely a filter -- it is what
            makes the partial HNSW index for that dimension eligible. Drop it and
            the planner falls back to a sequential scan.
          * No `u_id` predicate appears anywhere. RLS supplies it. If this query
            returns another tenant's row, RLS is misconfigured -- which is
            exactly the failure `verify_rls_enforced()` checks for at startup.
        """
        arr = np.asarray(query_vector, dtype=np.float32).ravel()
        if arr.shape[0] != dimension:
            raise ValueError(
                f"query vector dimension {arr.shape[0]} != expected {dimension}"
            )

        filters = ["dimension = :dim", "embedding_model = :model"]
        params: Dict[str, Any] = {
            "dim": dimension,
            "model": embedding_model,
            "qvec": to_pgvector(arr),
            "k": top_k,
        }
        if dataset_id:
            filters.append("dataset_id = CAST(:dataset_id AS uuid)")
            params["dataset_id"] = str(dataset_id)
        if template_id:
            filters.append("t_id = CAST(:template_id AS uuid)")
            params["template_id"] = str(template_id)

        sql = f"""
            SELECT row_uid, t_id, dataset_id, query, api_name, endpoint, method,
                   scenario_type, test_category, intent_type, notes,
                   embedding_model,
                   (embedding::vector({dimension}) <=> CAST(:qvec AS vector)) AS distance
            FROM {self.TABLE}
            WHERE {' AND '.join(filters)}
            ORDER BY embedding::vector({dimension}) <=> CAST(:qvec AS vector)
            LIMIT :k
        """

        t0 = time.perf_counter()
        result = await db.execute(text(sql), params)
        elapsed = (time.perf_counter() - t0) * 1000.0

        rows: List[Dict[str, Any]] = []
        for r in result.mappings():
            distance = float(r["distance"])
            rows.append(
                {
                    "row_uid": str(r["row_uid"]),
                    "t_id": str(r["t_id"]) if r["t_id"] else None,
                    "template_id": str(r["t_id"]) if r["t_id"] else None,
                    "dataset_id": str(r["dataset_id"]) if r["dataset_id"] else None,
                    "query": r["query"] or "",
                    "api_name": r["api_name"] or "",
                    "endpoint": r["endpoint"] or "",
                    "method": r["method"] or "POST",
                    "scenario_type": r["scenario_type"] or "valid",
                    "test_category": r["test_category"],
                    "intent_type": r["intent_type"],
                    "notes": r["notes"],
                    "embedding_model": r["embedding_model"],
                    # Same field names the cross-encoder and aggregator expect,
                    # so Stage 2 is agnostic to which backend fed it.
                    "similarity": 1.0 - distance,
                    "vector_score": distance,
                    "confidence_score": 0.7,
                }
            )

        if not rows:
            logger.warning(
                f"pgvector: 0 rows for model={embedding_model} dim={dimension}. "
                f"If the tenant demonstrably has data, check that the session was "
                f"opened via tenant_session() -- an unbound tenant GUC correctly "
                f"yields zero rows under RLS."
            )

        logger.info(f"pgvector: {len(rows)} candidates in {elapsed:.1f}ms")
        return VectorSearchResult(
            rows=rows, latency_ms=elapsed, dimension=dimension
        )

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    async def delete_by_dataset(self, db: AsyncSession, dataset_id: uuid.UUID) -> int:
        res = await db.execute(
            text(f"DELETE FROM {self.TABLE} WHERE dataset_id = CAST(:d AS uuid)"),
            {"d": str(dataset_id)},
        )
        return int(res.rowcount or 0)

    async def delete_by_template(self, db: AsyncSession, template_id: uuid.UUID) -> int:
        res = await db.execute(
            text(f"DELETE FROM {self.TABLE} WHERE t_id = CAST(:t AS uuid)"),
            {"t": str(template_id)},
        )
        return int(res.rowcount or 0)

    async def stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Per-model row counts for the caller's tenant (RLS-scoped)."""
        result = await db.execute(
            text(
                f"""
                SELECT embedding_model, dimension, COUNT(*) AS n
                FROM {self.TABLE}
                GROUP BY embedding_model, dimension
                ORDER BY n DESC
                """
            )
        )
        by_model = [
            {"model": r["embedding_model"], "dimension": r["dimension"], "rows": int(r["n"])}
            for r in result.mappings()
        ]
        return {"backend": "pgvector", "total_rows": sum(m["rows"] for m in by_model),
                "by_model": by_model}


_store: Optional[PgVectorStore] = None


def get_pgvector_store() -> PgVectorStore:
    global _store
    if _store is None:
        _store = PgVectorStore()
    return _store
