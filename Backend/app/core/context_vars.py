"""
context_vars.py — Request-scoped context propagation via Python contextvars.

Every async request carries a set of IDs that are automatically injected into
all structured log records emitted during that request's lifetime.

Hierarchy:
    correlation_id  — Highest-level business trace (can span multiple requests,
                      e.g. a Celery task triggered by an HTTP request). Set from
                      the incoming X-Correlation-ID header or generated fresh.
    request_id      — Unique per HTTP request / Celery task execution.
    trace_id        — OpenTelemetry W3C trace identifier (populated by OTel SDK).
    session_id      — Opaque session identifier forwarded from the frontend.
    user_id         — UUID of the authenticated user (None for anonymous).

Usage (middleware):
    from app.core.context_vars import set_request_context, clear_request_context

Usage (anywhere in the call stack):
    from app.core.context_vars import request_id_ctx
    current_rid = request_id_ctx.get()
"""

from contextvars import ContextVar
from typing import Optional

# ── Core identifiers ──────────────────────────────────────────────────────────

user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id_ctx", default=None)
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id_ctx", default=None)
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id_ctx", default=None)
trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id_ctx", default=None)
session_id_ctx: ContextVar[Optional[str]] = ContextVar("session_id_ctx", default=None)


# ── Helper: build a snapshot dict (for embedding in log records) ──────────────

def get_log_context() -> dict:
    """Return all active context variables as a dict suitable for log records."""
    return {
        "request_id": request_id_ctx.get(),
        "correlation_id": correlation_id_ctx.get(),
        "trace_id": trace_id_ctx.get(),
        "session_id": session_id_ctx.get(),
        "user_id": user_id_ctx.get(),
    }
