#!/usr/bin/env python
"""
Redis HNSW -> pgvector Backfill
===============================

Copies existing vectors out of the v1 Redis indexes into `vector_rows`.

WITHOUT THIS, PHASE 3 IS A DATA-LOSS EVENT. The migration creates an empty
table; every dataset a user already embedded would simply stop being findable,
with no error to explain why.

SAFETY PROPERTIES
-----------------
  * READ-ONLY against Redis. Nothing is deleted there. If the backfill is wrong,
    `VECTOR_BACKEND=redis` still works and you try again.
  * Idempotent. Rows are keyed by (u_id, t_id, query, embedding_model); a
    re-run updates rather than duplicating.
  * Per-tenant transactions. One tenant's bad data cannot roll back another's.
  * `--dry-run` reports exactly what would move and validates dimensions first.

WHY IT ITERATES PER TENANT
--------------------------
`vector_rows` is under RLS, and writes take `u_id` from the transaction's tenant
GUC rather than from a parameter. There is deliberately no way to bulk-insert
across tenants, so the backfill opens one tenant_session per user. That is
slower than a single COPY and is the correct trade: the same guarantee that
stops a router leaking data stops a migration script scrambling it.

USAGE
-----
    python scripts/backfill_redis_to_pgvector.py --dry-run
    python scripts/backfill_redis_to_pgvector.py
    python scripts/backfill_redis_to_pgvector.py --user <uuid>
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.logger import logger  # noqa: E402
from app.core.postgres import AsyncSessionLocal  # noqa: E402
from app.core.tenancy import tenant_session  # noqa: E402
from app.services.pgvector_store import get_pgvector_store  # noqa: E402

BATCH = 500


def scan_redis_vectors(
    redis_client: Any, only_user: Optional[uuid.UUID] = None
) -> Iterator[Dict[str, Any]]:
    """
    Stream every v1 embedding document out of Redis.

    SCAN, not KEYS: KEYS blocks the server for the whole keyspace walk, which on
    a production instance is an outage.
    """
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match="embedding:*", count=BATCH)
        for key in keys:
            key_s = key.decode() if isinstance(key, bytes) else key
            try:
                raw = redis_client.json().get(key_s)
            except Exception:  # noqa: BLE001 - non-JSON keys share the prefix
                continue
            if not isinstance(raw, dict) or "vector" not in raw:
                continue
            if only_user and str(raw.get("user_id")) != str(only_user):
                continue
            raw["_redis_key"] = key_s
            yield raw
        if cursor == 0:
            break


def group_by_tenant(docs: Iterator[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for doc in docs:
        uid = doc.get("user_id")
        if not uid:
            logger.warning(f"Skipping {doc.get('_redis_key')}: no user_id")
            continue
        grouped[str(uid)].append(doc)
    return grouped


def validate(docs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Reject rows that cannot be represented in pgvector.

    The important check is dimension consistency: v1 kept one Redis index per
    model, so a mixed-dimension bucket means the source data was already
    corrupt and must not be silently averaged into one table.
    """
    good: List[Dict[str, Any]] = []
    problems: List[str] = []
    dims_by_model: Dict[str, int] = {}

    for doc in docs:
        vec = doc.get("vector")
        model = doc.get("embedding_model")
        key = doc.get("_redis_key", "?")

        if not isinstance(vec, list) or not vec:
            problems.append(f"{key}: missing or empty vector")
            continue
        if not model:
            problems.append(f"{key}: no embedding_model — vector is unusable")
            continue
        if not doc.get("query"):
            problems.append(f"{key}: no query text — nothing for the reranker to score")
            continue

        dim = len(vec)
        seen = dims_by_model.setdefault(model, dim)
        if seen != dim:
            problems.append(
                f"{key}: model {model} has mixed dimensions ({seen} vs {dim})"
            )
            continue
        good.append(doc)

    return good, problems


async def backfill_tenant(
    tenant: uuid.UUID, docs: List[Dict[str, Any]], dry_run: bool
) -> Dict[str, int]:
    good, problems = validate(docs)
    for p in problems[:10]:
        logger.warning(f"  {p}")
    if len(problems) > 10:
        logger.warning(f"  ... and {len(problems) - 10} more")

    if dry_run:
        return {"would_write": len(good), "skipped": len(problems)}
    if not good:
        return {"written": 0, "skipped": len(problems)}

    by_model: Dict[Tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
    for doc in good:
        by_model[(doc["embedding_model"], len(doc["vector"]))].append(doc)

    store = get_pgvector_store()
    written = 0

    async with tenant_session(tenant) as db:
        for (model, dim), group in by_model.items():
            for i in range(0, len(group), BATCH):
                chunk = group[i : i + BATCH]
                rows = [
                    {
                        "t_id": d.get("template_id") or d.get("t_id"),
                        "dataset_id": d.get("dataset_id"),
                        "query": d.get("query", ""),
                        "api_name": d.get("api_name"),
                        "endpoint": d.get("endpoint"),
                        "method": d.get("method"),
                        "scenario_type": d.get("scenario_type", "valid"),
                        "test_category": d.get("test_category"),
                        "intent_type": d.get("intent_type"),
                        "notes": d.get("notes"),
                    }
                    for d in chunk
                ]
                vectors = [d["vector"] for d in chunk]
                written += await store.upsert_rows(
                    db, rows, vectors, embedding_model=model, dimension=dim
                )
            logger.info(f"  {model} ({dim}d): {len(group)} rows")

    return {"written": written, "skipped": len(problems)}


async def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill Redis vectors into pgvector")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--user", help="restrict to one tenant UUID")
    args = parser.parse_args(argv)

    only_user = uuid.UUID(args.user) if args.user else None

    try:
        from app.services.multi_model_redis_service import get_multi_model_redis_service

        redis_client = get_multi_model_redis_service().redis_client
        redis_client.ping()
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Cannot reach Redis: {exc}")
        return 1

    logger.info("Scanning Redis for v1 embeddings...")
    grouped = group_by_tenant(scan_redis_vectors(redis_client, only_user))
    if not grouped:
        logger.info("No v1 embeddings found — nothing to backfill.")
        return 0

    total_docs = sum(len(v) for v in grouped.values())
    logger.info(f"Found {total_docs} vectors across {len(grouped)} tenant(s)")
    if args.dry_run:
        logger.info("DRY RUN — nothing will be written")

    totals = {"written": 0, "would_write": 0, "skipped": 0}
    failures = 0

    for uid, docs in grouped.items():
        logger.info(f"Tenant {uid}: {len(docs)} vectors")
        try:
            result = await backfill_tenant(uuid.UUID(uid), docs, args.dry_run)
            for k, v in result.items():
                totals[k] = totals.get(k, 0) + v
        except Exception as exc:  # noqa: BLE001 - isolate per tenant
            failures += 1
            logger.error(f"Tenant {uid} FAILED (others continue): {exc}")

    logger.info(
        f"Backfill complete: {totals.get('written', totals.get('would_write', 0))} "
        f"rows, {totals['skipped']} skipped, {failures} tenant failure(s)"
    )
    if not args.dry_run:
        logger.info(
            "Redis was NOT modified. Verify with the eval harness, then set "
            "VECTOR_BACKEND=pgvector. Keep Redis data until you are satisfied."
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
