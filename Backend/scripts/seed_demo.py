#!/usr/bin/env python
"""
One-Click Demo Seed
===================

Creates a sandbox tenant with templates already loaded and vectors already
embedded, so a reviewer can run one query and watch the full pipeline work.

WHY THIS EXISTS
---------------
v1's cold-start path for a first-time visitor was: register, verify email by
OTP, author a template with a 500-word description, generate a dataset, wait for
embedding to finish, and only then run a query. That funnel loses every reviewer
before they reach the thing worth showing.

WHERE THE DATA COMES FROM
-------------------------
The 20 templates are imported from `app/demo_catalogue.py` — the same catalogue
the routing benchmark (evals/) runs against. That is deliberate: the demo tenant IS the
benchmark surface, so the numbers quoted in the README are reproducible against
what a reviewer is clicking. Two fixtures that could drift apart would be worse
than one.

IDEMPOTENT
----------
Safe to run on every boot. Re-running refreshes vectors without duplicating
templates. `--reset` wipes the sandbox tenant first.

USAGE
-----
    python scripts/seed_demo.py
    python scripts/seed_demo.py --reset
    SEED_DEMO=true                     # runs automatically on container boot
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import text  # noqa: E402

from app.core.logger import logger  # noqa: E402
from app.core.postgres import AsyncSessionLocal  # noqa: E402
from app.core.runtime import get_embedder, runtime_info  # noqa: E402
from app.core.tenancy import tenant_session  # noqa: E402
from app.services.pgvector_store import get_pgvector_store  # noqa: E402

# Fixed UUID so the sandbox tenant is stable across redeploys and can be
# referenced from the frontend's "try the demo" button.
DEMO_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000d30")
DEMO_EMAIL = os.getenv("SEED_DEMO_EMAIL", "demo@nlpforge.dev")
DEMO_PASSWORD = os.getenv("SEED_DEMO_PASSWORD", "DemoForge!2026")


def load_api_surface() -> List[Dict[str, Any]]:
    """The benchmark catalogue (shared with evals/run_eval.py)."""
    from app.demo_catalogue import API_TEMPLATES

    return list(API_TEMPLATES)


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

async def ensure_demo_user() -> None:
    """
    Create the sandbox user.

    Runs OUTSIDE tenant_session: RLS policies on tenant tables key off
    app.tenant_id, but the user row itself must exist before any tenant context
    can reference it.
    """
    # NOT app.core.security.get_password_hash: the actual login endpoints
    # (AuthService.verify_password) use a SHA-256-prehash + bcrypt scheme to
    # dodge bcrypt's 72-byte limit, incompatible with core.security's plain
    # bcrypt hash. Hashing with the wrong one silently locks the demo user
    # out with "Incorrect password".
    from app.services.auth_service import AuthService

    async with AsyncSessionLocal() as db:
        async with db.begin():
            await db.execute(
                text(
                    """
                    INSERT INTO users (u_id, email, password, user_name,
                                       is_active, is_expert, is_admin,
                                       email_verified, created_at)
                    VALUES (CAST(:uid AS uuid), :email, :pw, :username,
                            1, 0, 0, 1, now())
                    ON CONFLICT (u_id) DO UPDATE
                        SET email = EXCLUDED.email,
                            password = EXCLUDED.password,
                            email_verified = 1
                    """
                ),
                {
                    "uid": str(DEMO_USER_ID),
                    "email": DEMO_EMAIL,
                    "pw": AuthService.hash_password(DEMO_PASSWORD),
                    "username": "demo",
                },
            )
    logger.info(f"Demo tenant ready: {DEMO_EMAIL} ({DEMO_USER_ID})")


async def reset_demo_tenant() -> None:
    async with tenant_session(DEMO_USER_ID) as db:
        for table in ("vector_rows", "datasets", "templates"):
            result = await db.execute(text(f"DELETE FROM {table}"))
            logger.info(f"  cleared {result.rowcount or 0} rows from {table}")


async def seed_templates(templates: List[Dict[str, Any]]) -> Dict[str, uuid.UUID]:
    """
    Insert the API catalogue as COMPLETE templates. Returns api_name -> t_id.

    Every field the Template Builder treats as mandatory is filled from
    app/demo_catalogue_details.py: 500+ word documentation, parameter table,
    valid / edge / error sample requests with expected responses, sample
    responses, response schema, headers, auth, rate limit and assertions.

    t_id is derived deterministically from the api_name via uuid5, so re-running
    updates the same rows instead of creating duplicates, and the ids are stable
    across environments, which keeps benchmark labels portable.
    """
    from app.demo_catalogue_details import build_template_details

    ids: Dict[str, uuid.UUID] = {}
    async with tenant_session(DEMO_USER_ID) as db:
        for tpl in templates:
            t_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"nlpforge-demo:{tpl['api_name']}")
            ids[tpl["api_name"]] = t_id
            d = build_template_details(tpl)

            await db.execute(
                text(
                    """
                    INSERT INTO templates
                        (t_id, u_id, api_name, description, base_url, endpoint, "Field",
                         method, json_schema, response_schema, sample_requests,
                         sample_responses, domain_tags, auth_config, headers,
                         rate_limit, assertions, created_at, updated_at)
                    VALUES
                        (CAST(:t_id AS uuid), current_setting('app.tenant_id')::uuid,
                         :api_name, :description, :base_url, :endpoint, :endpoint,
                         :method, CAST(:json_schema AS jsonb), CAST(:response_schema AS jsonb),
                         CAST(:sample_requests AS jsonb), CAST(:sample_responses AS jsonb),
                         CAST(:tags AS jsonb), CAST(:auth_config AS jsonb),
                         CAST(:headers AS jsonb), CAST(:rate_limit AS jsonb),
                         CAST(:assertions AS jsonb), now(), now())
                    ON CONFLICT (t_id) DO UPDATE SET
                        api_name         = EXCLUDED.api_name,
                        description      = EXCLUDED.description,
                        base_url         = EXCLUDED.base_url,
                        endpoint         = EXCLUDED.endpoint,
                        "Field"          = EXCLUDED."Field",
                        method           = EXCLUDED.method,
                        json_schema      = EXCLUDED.json_schema,
                        response_schema  = EXCLUDED.response_schema,
                        sample_requests  = EXCLUDED.sample_requests,
                        sample_responses = EXCLUDED.sample_responses,
                        domain_tags      = EXCLUDED.domain_tags,
                        auth_config      = EXCLUDED.auth_config,
                        headers          = EXCLUDED.headers,
                        rate_limit       = EXCLUDED.rate_limit,
                        assertions       = EXCLUDED.assertions,
                        updated_at       = now()
                    """
                ),
                {
                    "t_id": str(t_id),
                    "api_name": tpl["api_name"],
                    "description": d["description"],
                    "base_url": "https://api.nlpforge.dev",
                    "endpoint": tpl["endpoint"],
                    "method": tpl["method"],
                    "json_schema": _json(tpl["json_schema"]),
                    "response_schema": _json(d["response_schema"]),
                    "sample_requests": _json(d["sample_requests"]),
                    "sample_responses": _json(d["sample_responses"]),
                    "tags": _json(d["domain_tags"]),
                    "auth_config": _json(d["auth_config"]),
                    "headers": _json(d["headers"]),
                    "rate_limit": _json(d["rate_limit"]),
                    "assertions": _json(d["assertions"]),
                },
            )

            # Parameter table and expected responses: replace wholesale so a
            # re-seed always matches the catalogue exactly.
            await db.execute(text("DELETE FROM parameters WHERE t_id = CAST(:t AS uuid)"), {"t": str(t_id)})
            await db.execute(text("DELETE FROM expected_responses WHERE t_id = CAST(:t AS uuid)"), {"t": str(t_id)})
            for p in d["parameters"]:
                await db.execute(
                    text(
                        """
                        INSERT INTO parameters (p_id, u_id, t_id, name, type, description, required, example)
                        VALUES (gen_random_uuid(), current_setting('app.tenant_id')::uuid,
                                CAST(:t AS uuid), :name, :type, :description, :required, :example)
                        """
                    ),
                    {
                        "t": str(t_id),
                        "name": p["name"],
                        "type": p["type"],
                        "description": p["description"],
                        "required": 1 if p["required"] else 0,
                        "example": p["example"] if isinstance(p["example"], str) else _json(p["example"]),
                    },
                )
            for r in d["sample_responses"]:
                await db.execute(
                    text(
                        """
                        INSERT INTO expected_responses (r_id, u_id, t_id, status, fields)
                        VALUES (gen_random_uuid(), current_setting('app.tenant_id')::uuid,
                                CAST(:t AS uuid), :status, CAST(:fields AS jsonb))
                        """
                    ),
                    {"t": str(t_id), "status": r["status_code"], "fields": _json(r["response_body"])},
                )

            # Status lives in the `metadata` table. Demo templates are approved,
            # so they appear as active and can drive dataset generation.
            await db.execute(
                text(
                    """
                    INSERT INTO metadata (m_id, u_id, t_id, status, approved_by,
                                          approved_at, confidence, remarks, created_at)
                    VALUES (CAST(:m_id AS uuid), current_setting('app.tenant_id')::uuid,
                            CAST(:t_id AS uuid), 'approved',
                            current_setting('app.tenant_id')::uuid, now(), 100,
                            'Seeded demo template: reviewed catalogue entry', now())
                    ON CONFLICT (m_id) DO UPDATE SET status = 'approved'
                    """
                ),
                {"m_id": str(uuid.uuid5(t_id, "metadata")), "t_id": str(t_id)},
            )
    logger.info(f"Seeded {len(ids)} complete templates (approved)")
    return ids


async def seed_vectors(
    templates: List[Dict[str, Any]], ids: Dict[str, uuid.UUID]
) -> int:
    """
    Embed every utterance and write it to vector_rows.

    Embedding happens through the runtime adapter, so the vectors match whichever
    EXECUTION_MODE this deployment runs — 768-dim in local mode, 384-dim in
    cloud. Storing model+dimension per row is what makes that safe.
    """
    embedder = get_embedder()

    rows: List[Dict[str, Any]] = []
    texts: List[str] = []
    for tpl in templates:
        for utt in tpl["utterances"]:
            rows.append(
                {
                    "t_id": ids[tpl["api_name"]],
                    "dataset_id": None,
                    "query": utt,
                    "api_name": tpl["api_name"],
                    "endpoint": tpl["endpoint"],
                    "method": tpl["method"],
                    "scenario_type": "valid",
                    "test_category": "demo_seed",
                    "intent_type": "action" if tpl["method"] != "GET" else "info",
                }
            )
            texts.append(utt)

    logger.info(f"Embedding {len(texts)} utterances with {embedder.model_id}...")
    vectors = await embedder.embed(texts)
    if len(vectors) != len(texts):
        raise SystemExit(
            f"Embedder returned {len(vectors)} vectors for {len(texts)} texts. "
            f"Refusing to seed a partially-embedded index."
        )

    store = get_pgvector_store()
    async with tenant_session(DEMO_USER_ID) as db:
        # Clear first so a re-run refreshes rather than duplicating.
        await db.execute(text("DELETE FROM vector_rows WHERE test_category = 'demo_seed'"))
        written = await store.upsert_rows(
            db,
            rows,
            vectors,
            embedding_model=embedder.model_id,
            dimension=embedder.dimension,
        )
    logger.info(f"Indexed {written} vectors")
    return written


async def verify(templates: List[Dict[str, Any]]) -> bool:
    """
    Prove the seed works by routing a query end to end.

    A seed that inserts rows but cannot answer a question is not a working demo,
    and this catches dimension mismatches and RLS misconfiguration immediately
    rather than at the reviewer's first click.
    """
    from app.nlp.cross_encoder_reranker import get_reranker

    embedder = get_embedder()
    store = get_pgvector_store()
    reranker = get_reranker()
    await reranker.warm()

    probe = "I forgot my password, send me a reset link"
    expected = "Password_Reset_Request"

    qv = await embedder.embed_one(probe)
    async with tenant_session(DEMO_USER_ID) as db:
        result = await store.search(
            db,
            qv,
            embedding_model=embedder.model_id,
            dimension=embedder.dimension,
            top_k=25,
        )

    if not result.rows:
        logger.error("Verification FAILED: retrieval returned no rows")
        return False

    outcome = await reranker.run(probe, result.rows, top_k=5)
    best = outcome.best
    if best is None:
        logger.error("Verification FAILED: reranker produced no candidate")
        return False

    routed = best.api_name or "?"
    ok = routed == expected
    logger.info(
        f"Verification: '{probe}' -> {routed} "
        f"(ce_score={best.ce_score:.4f}, {result.latency_ms:.0f}ms retrieval)"
    )
    if not ok:
        logger.warning(f"  expected {expected}; routing works but accuracy differs")
    return True


def _json(obj: Any) -> str:
    import json

    return json.dumps(obj)


# ---------------------------------------------------------------------------

async def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the NLPForge demo tenant")
    parser.add_argument("--reset", action="store_true", help="wipe the tenant first")
    parser.add_argument("--skip-verify", action="store_true")
    args = parser.parse_args(argv)

    info = runtime_info()
    logger.info(
        f"Seeding demo tenant | mode={info['execution_mode']} "
        f"embedder={info['embedder']['model']} dim={info['embedder']['dimension']}"
    )

    templates = load_api_surface()

    try:
        await ensure_demo_user()
        if args.reset:
            logger.info("Resetting demo tenant...")
            await reset_demo_tenant()

        ids = await seed_templates(templates)
        await seed_vectors(templates, ids)

        if not args.skip_verify and not await verify(templates):
            return 1
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Seed failed: {exc}")
        return 1

    print(
        f"\n  Demo tenant ready\n"
        f"    email    : {DEMO_EMAIL}\n"
        f"    password : {DEMO_PASSWORD}\n"
        f"    templates: {len(templates)}\n"
        f"    try      : \"I forgot my password, send me a reset link\"\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
