"""
celery_app.py — Celery application factory for NLPForge

Broker:  Redis DB 1  (DB 0 is reserved for vector embeddings / RedisSearch)
Backend: Redis DB 2  (task result state — replaces in-memory _task_store)

Usage inside tasks:
    from app.worker.celery_app import celery_app

Usage from FastAPI (triggering):
    from app.worker.tasks import generate_dataset_task
    result = generate_dataset_task.delay(payload)
    task_id = result.id  # standard Celery UUID
"""

import os
from celery import Celery

# ---------------------------------------------------------------------------
# Redis connection — uses the same Redis instance already in docker-compose.
# DB 0 → RedisSearch / vector embeddings (existing)
# DB 1 → Celery broker queue
# DB 2 → Celery task result backend
# ---------------------------------------------------------------------------
_redis_password = os.getenv("REDIS_PASSWORD", "nlpforgeRedis2024")
_redis_host = os.getenv("REDIS_HOST", "redis")
_redis_port = os.getenv("REDIS_PORT", "6379")

CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    f"redis://:{_redis_password}@{_redis_host}:{_redis_port}/1",
)
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    f"redis://:{_redis_password}@{_redis_host}:{_redis_port}/2",
)

celery_app = Celery(
    "nlpforge",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    # Autodiscover tasks only from this module — avoids accidental imports
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    # ── Serialisation ───────────────────────────────────────────────────────
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # ── Timezone ────────────────────────────────────────────────────────────
    timezone="UTC",
    enable_utc=True,

    # ── Result TTL ──────────────────────────────────────────────────────────
    # Keep task results in Redis for 24 hours — enough for the UI to poll.
    result_expires=86400,

    # ── Worker behaviour ────────────────────────────────────────────────────
    # Each worker prefetches only 1 task at a time.  Long-running LLM jobs
    # should not block shorter tasks queued behind them.
    worker_prefetch_multiplier=1,
    task_acks_late=True,          # Acknowledge AFTER completion, not on pickup
    task_reject_on_worker_lost=True,  # Requeue if worker dies mid-task

    # ── Routing — single default queue for now ───────────────────────────
    task_default_queue="nlpforge",

    # ── Progress meta updates ────────────────────────────────────────────
    # Allow tasks to call self.update_state() to push progress to the backend
    task_track_started=True,
)
