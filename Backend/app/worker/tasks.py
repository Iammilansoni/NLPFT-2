"""
tasks.py — Celery task definitions for NLPForge

All tasks here are SYNCHRONOUS from Celery's perspective.
Heavy async logic (LLM calls) is run via asyncio.run() inside the task.

DB access inside the worker uses a SYNC SQLAlchemy engine (psycopg2) because
Celery workers do not have a running event loop at the module level.

Progress updates are pushed to the Celery result backend via self.update_state().
The FastAPI status endpoint reads these via AsyncResult(task_id).info.

Task payload contract (DatasetGeneratePayload):
    {
        "template_data":          dict,
        "num_examples":           int | None,
        "user_prompt":            str,
        "focus_areas":            list[str] | None,
        "scenario_distribution":  dict | None,
        "user_id":                str,    # UUID as string
        "template_id":            str,    # UUID as string
        "dataset_name":           str,
    }
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from celery import Task
from celery.utils.log import get_task_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.worker.celery_app import celery_app

logger = get_task_logger(__name__)


# ---------------------------------------------------------------------------
# Sync DB engine — workers live outside FastAPI's event loop.
# SYNC_DATABASE_URL must use the psycopg2 driver (no +asyncpg).
# ---------------------------------------------------------------------------

def _get_sync_db_url() -> str:
    """
    Return a synchronous (psycopg2) DATABASE_URL for use in Celery workers.

    Priority:
    1. SYNC_DATABASE_URL env var (explicit, preferred)
    2. DATABASE_URL with '+asyncpg' stripped out
    """
    sync_url = os.getenv("SYNC_DATABASE_URL")
    if sync_url:
        return sync_url

    async_url = os.getenv("DATABASE_URL", "")
    if not async_url:
        # Fall back to building from parts
        user = os.getenv("POSTGRES_USER", "nlpforge")
        pw = os.getenv("POSTGRES_PASSWORD", "")
        host = os.getenv("POSTGRES_HOST", "postgres")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "nlpforge")
        return f"postgresql://{user}:{pw}@{host}:{port}/{db}"

    return async_url.replace("+asyncpg", "")


def _make_sync_session_factory() -> sessionmaker:
    """Create a synchronous SQLAlchemy session factory (psycopg2 driver)."""
    url = _get_sync_db_url()
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_size=2,       # Workers are long-lived; keep the pool small
        max_overflow=3,
    )
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Lazily initialised on first task execution (not at import time)
_SyncSessionFactory: Optional[sessionmaker] = None


def get_sync_session() -> Session:
    """Get a synchronous DB session. Creates the engine on first call."""
    global _SyncSessionFactory
    if _SyncSessionFactory is None:
        _SyncSessionFactory = _make_sync_session_factory()
    return _SyncSessionFactory()


# ---------------------------------------------------------------------------
# Base task class — provides shared helpers
# ---------------------------------------------------------------------------

class NLPForgeTask(Task):
    """Base Celery task that pushes structured progress to the result backend."""

    abstract = True

    def push_progress(
        self,
        progress: int,
        message: str,
        step: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Push a progress update to the Celery result backend.
        FastAPI reads this via AsyncResult(task_id).info.
        """
        meta = {
            "progress": min(100, max(0, progress)),
            "message": message,
            "current_step": step,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            meta.update(extra)
        self.update_state(state="PROGRESS", meta=meta)


# ---------------------------------------------------------------------------
# Dataset generation task
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    base=NLPForgeTask,
    name="nlpforge.generate_dataset",
    max_retries=0,           # LLM jobs are expensive; don't auto-retry blindly
    soft_time_limit=1800,    # 30 min soft limit — sends SoftTimeLimitExceeded
    time_limit=2100,         # 35 min hard kill
)
def generate_dataset_task(self: NLPForgeTask, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task: generate an NLP dataset from a template using an LLM provider.

    Replaces _run_generation_background() + asyncio.ensure_future() in datasets.py.
    Runs synchronously in the worker process. Async LLM calls are wrapped with
    asyncio.run() — safe here because the worker has no running event loop.

    Args:
        payload: See module-level docstring for the payload contract.

    Returns:
        Dict with generation results (also stored in Redis result backend).
    """
    task_id = self.request.id
    logger.info(f"[{task_id}] Dataset generation task started")

    # ── Unpack payload ────────────────────────────────────────────────────
    template_data: Dict = payload["template_data"]
    num_examples: Optional[int] = payload.get("num_examples")
    user_prompt: str = payload.get("user_prompt", "")
    focus_areas = payload.get("focus_areas")
    scenario_distribution = payload.get("scenario_distribution")
    user_id_str: str = payload["user_id"]
    template_id_str: str = payload["template_id"]
    dataset_name: str = payload.get("dataset_name", "generated_dataset")

    user_id_uuid = uuid.UUID(user_id_str)
    template_id_uuid = uuid.UUID(template_id_str)

    self.push_progress(5, "Task received by worker, initializing...", "init")

    # ── Step 1: Run LLM generation + audit log (single event loop) ─────────
    # Both async operations share one asyncio.run() call — avoids creating
    # and tearing down two separate event loops (and asyncpg pools) per task.
    try:
        result = asyncio.run(
            _run_generation_and_audit_async(
                task=self,
                template_data=template_data,
                num_examples=num_examples,
                user_prompt=user_prompt,
                focus_areas=focus_areas,
                scenario_distribution=scenario_distribution,
                user_id_str=user_id_str,
                user_id_uuid=user_id_uuid,
                template_id_uuid=template_id_uuid,
            )
        )
    except Exception as exc:
        logger.exception(f"[{task_id}] LLM generation failed: {exc}")
        raise

    if not result.get("success"):
        # Surface the structured error from the generator
        error_msg = result.get("error", "Unknown generation error")
        logger.error(f"[{task_id}] Generator returned failure: {error_msg}")
        # Raising an exception marks the Celery task as FAILURE state
        raise RuntimeError(error_msg)

    csv_path: str = result["paths"]["csv"]
    self.push_progress(75, f"Generated {result['total_generated']} test cases. Saving to database...", "store_db")

    # ── Step 2: Store CSV rows in PostgreSQL ──────────────────────────────
    # Uses a synchronous session because we're outside the async event loop.
    dataset_id = None
    db: Optional[Session] = None
    try:
        db = get_sync_session()
        dataset_id = _store_csv_to_postgresql_sync(
            db=db,
            csv_path=csv_path,
            user_id=user_id_uuid,
            template_id=template_id_uuid,
            dataset_name=f"{dataset_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            generated_with_llm=result.get("model_used"),
            generation_prompt=user_prompt,
            scenario_distribution=result.get("scenario_distribution"),
        )
        logger.info(f"[{task_id}] Stored dataset in PostgreSQL (dataset_id={dataset_id})")
    except Exception as exc:
        logger.exception(f"[{task_id}] Failed to store dataset in PostgreSQL: {exc}")
        raise RuntimeError(f"Database storage failed: {exc}") from exc
    finally:
        if db:
            db.close()

    self.push_progress(100, f"Done. {result['total_generated']} test cases ready.", "complete")

    # ── Return value is stored in the Celery result backend ───────────────
    return {
        "success": True,
        "task_id": task_id,
        "dataset_id": str(dataset_id) if dataset_id else None,
        "total_generated": result["total_generated"],
        "csv_path": csv_path,
        "template_name": result["template_name"],
        "template_id": template_id_str,
        "requested": result["requested"],
        "scenario_distribution": result["scenario_distribution"],
        "category_distribution": result["category_distribution"],
        "csv_preview": result.get("csv_preview", []),
        "model_used": result.get("model_used"),
        "download_url": f"/v1/datasets/download/{os.path.basename(csv_path)}",
        "stored_in_postgresql": dataset_id is not None,
        "embedding_status": "pending",
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _run_generation_and_audit_async(
    task: NLPForgeTask,
    template_data: Dict,
    num_examples: Optional[int],
    user_prompt: str,
    focus_areas,
    scenario_distribution,
    user_id_str: str,
    user_id_uuid: uuid.UUID,
    template_id_uuid: uuid.UUID,
) -> Dict[str, Any]:
    """
    Single async coroutine that runs LLM generation + audit log.
    Called via ONE asyncio.run() in generate_dataset_task to avoid
    creating multiple event loops (and asyncpg pools) per task execution.
    """
    from app.nlp.dataset_generator import get_enterprise_dataset_generator
    from app.core.postgres import AsyncSessionLocal
    from app.services.audit_service import get_audit_service

    task.push_progress(10, "Loading LLM provider configuration...", "load_provider")
    generator = get_enterprise_dataset_generator()

    async with AsyncSessionLocal() as db:
        result = await generator.generate_dataset_from_template(
            template_data=template_data,
            num_examples=num_examples,
            user_prompt=user_prompt,
            focus_areas=focus_areas,
            scenario_distribution=scenario_distribution,
            task_id=None,
            user_id=user_id_str,
            db=db,
        )

    # Audit log runs in the SAME event loop — no second asyncio.run()
    if result.get("success"):
        try:
            audit_service = get_audit_service()
            async with AsyncSessionLocal() as audit_db:
                await audit_service.log_dataset_generated(
                    db=audit_db,
                    user_id=user_id_uuid,
                    template_id=template_id_uuid,
                    dataset_path=result["paths"]["csv"],
                    num_examples=result["total_generated"],
                    metadata_={
                        "template_name": result["template_name"],
                        "user_prompt": user_prompt[:200],
                        "scenario_distribution": result["scenario_distribution"],
                        "embedding_status": "pending",
                    },
                    request=None,
                )
        except Exception as exc:
            logger.warning(f"Audit log failed (non-fatal): {exc}")

    return result


def _store_csv_to_postgresql_sync(
    db: Session,
    csv_path: str,
    user_id: uuid.UUID,
    template_id: uuid.UUID,
    dataset_name: str,
    generated_with_llm: Optional[str],
    generation_prompt: Optional[str],
    scenario_distribution: Optional[dict],
) -> uuid.UUID:
    """
    Synchronous version of store_csv_to_postgresql for use inside Celery tasks.

    Returns the new dataset_id UUID.
    """
    import json
    import pandas as pd
    from datetime import datetime, timezone
    from app.models.database_models import Dataset, CSVData

    df = pd.read_csv(csv_path)
    if "query" in df.columns:
        df = df.dropna(subset=["query"])
    total_rows = len(df)

    logger.info(f"Storing {total_rows} CSV rows to PostgreSQL (sync)...")

    dataset_id = uuid.uuid4()
    dataset = Dataset(
        dataset_id=dataset_id,
        u_id=user_id,
        t_id=template_id,
        name=dataset_name,
        csv_path=csv_path,
        total_rows=total_rows,
        embedding_status="pending",
        embedding_progress=0,
        embedded_rows=0,
        generated_with_llm=generated_with_llm,
        generation_prompt=generation_prompt,
        scenario_distribution=scenario_distribution,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(dataset)
    db.flush()  # Obtain dataset.dataset_id PK

    csv_rows = []
    for idx, row in df.iterrows():
        request_data = None
        response_data = None

        if "request" in df.columns and pd.notna(row.get("request")):
            try:
                request_data = (
                    json.loads(row["request"])
                    if isinstance(row["request"], str)
                    else row["request"]
                )
            except (json.JSONDecodeError, TypeError):
                request_data = {"raw": str(row["request"])}

        if "response" in df.columns and pd.notna(row.get("response")):
            try:
                response_data = (
                    json.loads(row["response"])
                    if isinstance(row["response"], str)
                    else row["response"]
                )
            except (json.JSONDecodeError, TypeError):
                response_data = {"raw": str(row["response"])}

        csv_rows.append(
            CSVData(
                csv_id=uuid.uuid4(),
                u_id=user_id,
                t_id=template_id,
                dataset_id=dataset_id,
                query=str(row.get("query", "")) if pd.notna(row.get("query")) else None,
                api_name=str(row.get("api", "")) if pd.notna(row.get("api")) else None,
                endpoint=str(row.get("endpoint", "")) if pd.notna(row.get("endpoint")) else None,
                request=request_data,
                response=response_data,
                description=str(row.get("notes", "")) if pd.notna(row.get("notes")) else None,
                data_category=str(row.get("scenario_type", "valid")) if pd.notna(row.get("scenario_type")) else "valid",
                variation_type=str(row.get("test_category", "")) if pd.notna(row.get("test_category")) else None,
                generated_with_llm=generated_with_llm,
                generation_prompt=generation_prompt,
                is_embedded=0,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )

        if len(csv_rows) >= 100:
            db.add_all(csv_rows)
            db.flush()
            csv_rows = []

    if csv_rows:
        db.add_all(csv_rows)

    db.commit()
    logger.info(f"Stored {total_rows} rows in PostgreSQL (dataset_id={dataset_id})")
    return dataset_id



