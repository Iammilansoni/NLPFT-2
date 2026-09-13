"""
metrics.py — Prometheus metrics for NLPForge backend.

Exports a /api/v1/metrics endpoint that Prometheus scrapes every 15 seconds.

Metric naming follows Prometheus conventions:
  nlpforge_http_requests_total           — counter
  nlpforge_http_request_duration_ms      — histogram
  nlpforge_llm_requests_total            — counter
  nlpforge_llm_request_duration_ms       — histogram
  nlpforge_embedding_requests_total      — counter
  nlpforge_celery_tasks_total            — counter
  nlpforge_celery_queue_length_gauge     — gauge
  nlpforge_auth_events_total             — counter
  nlpforge_health_check_status           — gauge (1=healthy, 0=unhealthy)
  nlpforge_db_pool_size_gauge            — gauge
  nlpforge_db_pool_available_gauge       — gauge

USAGE (instrument a function):
    from app.core.metrics import (
        record_http_request, record_llm_request, record_auth_event
    )
    record_http_request("GET", "/api/v1/datasets", 200, 123.4)
    record_llm_request("openai", "gpt-4o", True, 4500.0)
    record_auth_event("login_success", user_id="...")
"""

import time
from typing import Optional

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        REGISTRY,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from app.core.logger import get_logger

logger = get_logger(__name__)

if not PROMETHEUS_AVAILABLE:
    logger.warning(
        "prometheus_client not installed — metrics endpoint will be unavailable. "
        "Add 'prometheus-client>=0.20.0' to requirements.txt.",
        extra={"extra": {
            "event_name": "metrics_init",
            "status": "unavailable",
            "suggested_fix": "pip install prometheus-client>=0.20.0",
        }},
    )


# ── Metric definitions (only initialised if prometheus_client is available) ───

if PROMETHEUS_AVAILABLE:

    # ── HTTP ─────────────────────────────────────────────────────────────────
    HTTP_REQUESTS = Counter(
        "nlpforge_http_requests_total",
        "Total HTTP requests processed",
        ["method", "path", "status_code"],
    )

    HTTP_DURATION = Histogram(
        "nlpforge_http_request_duration_ms",
        "HTTP request duration in milliseconds",
        ["method", "path"],
        buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000],
    )

    # ── LLM Providers ────────────────────────────────────────────────────────
    LLM_REQUESTS = Counter(
        "nlpforge_llm_requests_total",
        "Total LLM API requests",
        ["provider", "model", "status"],
    )

    LLM_DURATION = Histogram(
        "nlpforge_llm_request_duration_ms",
        "LLM request duration in milliseconds",
        ["provider", "model"],
        buckets=[500, 1000, 2500, 5000, 10000, 30000, 60000, 120000],
    )

    LLM_TOKEN_USAGE = Counter(
        "nlpforge_llm_tokens_total",
        "Total LLM tokens consumed",
        ["provider", "model", "token_type"],
    )

    # ── Embeddings ────────────────────────────────────────────────────────────
    EMBEDDING_REQUESTS = Counter(
        "nlpforge_embedding_requests_total",
        "Total embedding generation requests",
        ["model", "status"],
    )

    EMBEDDING_DURATION = Histogram(
        "nlpforge_embedding_request_duration_ms",
        "Embedding generation duration in milliseconds",
        ["model"],
        buckets=[50, 100, 250, 500, 1000, 2500, 5000, 15000],
    )

    # ── Celery Workers ────────────────────────────────────────────────────────
    CELERY_TASKS = Counter(
        "nlpforge_celery_tasks_total",
        "Total Celery tasks",
        ["task_name", "status"],
    )

    CELERY_TASK_DURATION = Histogram(
        "nlpforge_celery_task_duration_ms",
        "Celery task duration in milliseconds",
        ["task_name"],
        buckets=[1000, 5000, 15000, 30000, 60000, 300000, 600000],
    )

    CELERY_QUEUE_LENGTH = Gauge(
        "nlpforge_celery_queue_length_gauge",
        "Number of pending Celery tasks in queue",
    )

    # ── Authentication ─────────────────────────────────────────────────────
    AUTH_EVENTS = Counter(
        "nlpforge_auth_events_total",
        "Authentication events",
        ["event", "client_ip"],
    )

    # ── Health ────────────────────────────────────────────────────────────────
    HEALTH_STATUS = Gauge(
        "nlpforge_health_check_status",
        "Service health status (1=healthy, 0=unhealthy)",
        ["service"],
    )

    # ── Database Pool ─────────────────────────────────────────────────────────
    DB_POOL_SIZE = Gauge(
        "nlpforge_db_pool_size_gauge",
        "Total DB connection pool size",
    )

    DB_POOL_AVAILABLE = Gauge(
        "nlpforge_db_pool_available_gauge",
        "Available DB connections in pool",
    )

    # ── Vector Search ─────────────────────────────────────────────────────────
    VECTOR_SEARCH = Counter(
        "nlpforge_vector_search_total",
        "Total vector search operations",
        ["model", "status"],
    )

    VECTOR_SEARCH_DURATION = Histogram(
        "nlpforge_vector_search_duration_ms",
        "Vector search duration in milliseconds",
        ["model"],
        buckets=[5, 10, 25, 50, 100, 250, 500, 1000, 2500],
    )


# ── Recorder functions ────────────────────────────────────────────────────────

def record_http_request(method: str, path: str, status_code: int, duration_ms: float):
    if not PROMETHEUS_AVAILABLE:
        return
    # Normalise path to avoid cardinality explosion (strip UUIDs/IDs)
    import re
    normalised = re.sub(r"/[0-9a-f-]{8,}", "/{id}", path)
    HTTP_REQUESTS.labels(method=method, path=normalised, status_code=str(status_code)).inc()
    HTTP_DURATION.labels(method=method, path=normalised).observe(duration_ms)


def record_llm_request(
    provider: str,
    model: str,
    success: bool,
    duration_ms: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
):
    if not PROMETHEUS_AVAILABLE:
        return
    status = "success" if success else "failure"
    LLM_REQUESTS.labels(provider=provider, model=model, status=status).inc()
    LLM_DURATION.labels(provider=provider, model=model).observe(duration_ms)
    if prompt_tokens:
        LLM_TOKEN_USAGE.labels(provider=provider, model=model, token_type="prompt").inc(prompt_tokens)
    if completion_tokens:
        LLM_TOKEN_USAGE.labels(provider=provider, model=model, token_type="completion").inc(completion_tokens)


def record_embedding_request(model: str, success: bool, duration_ms: float):
    if not PROMETHEUS_AVAILABLE:
        return
    status = "success" if success else "failure"
    EMBEDDING_REQUESTS.labels(model=model, status=status).inc()
    EMBEDDING_DURATION.labels(model=model).observe(duration_ms)


def record_celery_task(task_name: str, success: bool, duration_ms: float):
    if not PROMETHEUS_AVAILABLE:
        return
    status = "success" if success else "failure"
    CELERY_TASKS.labels(task_name=task_name, status=status).inc()
    CELERY_TASK_DURATION.labels(task_name=task_name).observe(duration_ms)


def record_auth_event(event: str, client_ip: str = "unknown"):
    if not PROMETHEUS_AVAILABLE:
        return
    AUTH_EVENTS.labels(event=event, client_ip=client_ip).inc()


def set_health_status(service: str, healthy: bool):
    if not PROMETHEUS_AVAILABLE:
        return
    HEALTH_STATUS.labels(service=service).set(1 if healthy else 0)


def set_celery_queue_length(length: int):
    if not PROMETHEUS_AVAILABLE:
        return
    CELERY_QUEUE_LENGTH.set(length)


def record_vector_search(model: str, success: bool, duration_ms: float):
    if not PROMETHEUS_AVAILABLE:
        return
    status = "success" if success else "failure"
    VECTOR_SEARCH.labels(model=model, status=status).inc()
    VECTOR_SEARCH_DURATION.labels(model=model).observe(duration_ms)


# ── FastAPI /metrics route ────────────────────────────────────────────────────

from fastapi import APIRouter, Response

metrics_router = APIRouter()


@metrics_router.get(
    "/metrics",
    tags=["Observability"],
    summary="Prometheus metrics endpoint",
    include_in_schema=False,  # Don't expose in Swagger (internal use only)
)
async def prometheus_metrics():
    """Expose Prometheus-compatible metrics for scraping."""
    if not PROMETHEUS_AVAILABLE:
        return Response(
            content="# prometheus_client not installed\n",
            media_type="text/plain",
            status_code=503,
        )
    from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
