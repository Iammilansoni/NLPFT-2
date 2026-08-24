"""
tracing.py — Lightweight distributed tracing for NLPForge.

APPROACH
--------
Phase 1 (this file): Pure Python implementation using contextvars + UUIDs.
    - Generates W3C-compatible trace_id and span_id without any external SDK.
    - Injects IDs into all log records automatically via context_vars.
    - Attaches X-Request-ID, X-Trace-ID, X-Correlation-ID response headers.
    - Zero new pip dependencies.

Phase 2 (future): Drop-in replacement with opentelemetry-sdk + Tempo exporter.
    - Replace TraceContext with real OTel spans.
    - The middleware signature stays identical.

USAGE
-----
The middleware is registered in main.py. After that, every piece of code that
calls `get_log_context()` or reads from context_vars gets the IDs for free.

For manual span creation (coarse-grained timing):
    from app.core.tracing import start_span, finish_span
    span_id = start_span("embedding_generation")
    ...
    finish_span(span_id, success=True)
"""

import os
import secrets
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.context_vars import (
    correlation_id_ctx,
    request_id_ctx,
    session_id_ctx,
    trace_id_ctx,
    user_id_ctx,
)
from app.core.logger import get_logger

# Import metrics recorder (gracefully absent if prometheus_client not installed)
try:
    from app.core.metrics import record_http_request as _record_http
except ImportError:
    _record_http = None

logger = get_logger(__name__)


# ── ID generation ─────────────────────────────────────────────────────────────

def new_request_id() -> str:
    """Generate a short unique request identifier (hex, 16 chars)."""
    return secrets.token_hex(8)  # 8 bytes → 16 hex chars


def new_trace_id() -> str:
    """Generate a W3C-compatible trace ID (hex, 32 chars)."""
    return secrets.token_hex(16)  # 128-bit trace ID


def new_span_id() -> str:
    """Generate a W3C-compatible span ID (hex, 16 chars)."""
    return secrets.token_hex(8)


# ── Span tracking (lightweight manual spans) ──────────────────────────────────

@dataclass
class Span:
    name: str
    span_id: str = field(default_factory=new_span_id)
    started_at: float = field(default_factory=time.monotonic)
    tags: dict = field(default_factory=dict)
    success: Optional[bool] = None
    error_message: Optional[str] = None
    finished_at: Optional[float] = None

    @property
    def duration_ms(self) -> Optional[float]:
        if self.finished_at is None:
            return None
        return round((self.finished_at - self.started_at) * 1000, 3)


# In-process span registry (keyed by span_id)
_active_spans: dict[str, Span] = {}


def start_span(name: str, **tags) -> str:
    """Start a named span and return its ID. Call finish_span() when done."""
    span = Span(name=name, tags=tags)
    _active_spans[span.span_id] = span
    logger.debug(
        f"span_start name={name} span_id={span.span_id}",
        extra={"extra": {"event_name": "span_start", "span_name": name, "span_id": span.span_id, **tags}},
    )
    return span.span_id


def finish_span(span_id: str, *, success: bool = True, error: Optional[str] = None) -> Optional[float]:
    """Finish a span and log it. Returns duration_ms or None if not found."""
    span = _active_spans.pop(span_id, None)
    if span is None:
        return None
    span.finished_at = time.monotonic()
    span.success = success
    span.error_message = error

    level = "INFO" if success else "WARNING"
    logger.log(
        __import__("logging").getLevelName(level),
        f"span_end name={span.name} duration_ms={span.duration_ms} success={success}",
        extra={"extra": {
            "event_name": "span_end",
            "span_name": span.name,
            "span_id": span_id,
            "duration_ms": span.duration_ms,
            "success": success,
            "error": error,
        }},
    )
    return span.duration_ms


@asynccontextmanager
async def trace_span(name: str, **tags) -> AsyncIterator[str]:
    """Async context manager for automatic span lifecycle management."""
    sid = start_span(name, **tags)
    try:
        yield sid
        finish_span(sid, success=True)
    except Exception as exc:
        finish_span(sid, success=False, error=str(exc))
        raise


# ── ASGI Middleware ───────────────────────────────────────────────────────────

class TracingMiddleware(BaseHTTPMiddleware):
    """
    Per-request middleware that:
    1.  Extracts or generates request_id, correlation_id, trace_id, session_id.
    2.  Injects them into contextvars so every logger in the request sees them.
    3.  Adds X-Request-ID, X-Trace-ID, X-Correlation-ID to the response.
    4.  Logs a structured access record (method, path, status, duration_ms).
    5.  Resets all context vars on request completion.
    """

    SKIP_PATHS = {"/api/v1/health", "/api/v1/health/postgres", "/api/v1/health/redis", "/"}

    def __init__(self, app: ASGIApp, service_name: str = "nlpforge-backend"):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # --- Read or generate IDs ---
        request_id    = request.headers.get("X-Request-ID") or new_request_id()
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or request_id
        )
        # W3C traceparent extraction (if present): "00-{trace_id}-{span_id}-{flags}"
        traceparent = request.headers.get("traceparent", "")
        if traceparent and len(traceparent.split("-")) == 4:
            _, trace_id, _, _ = traceparent.split("-")
        else:
            trace_id = new_trace_id()

        session_id = request.headers.get("X-Session-ID")

        # --- Set context vars (tokens let us reset after the request) ---
        tok_rid  = request_id_ctx.set(request_id)
        tok_cid  = correlation_id_ctx.set(correlation_id)
        tok_tid  = trace_id_ctx.set(trace_id)
        tok_sid  = session_id_ctx.set(session_id)

        # --- Authenticate user_id from token (best-effort) ---
        tok_uid  = user_id_ctx.set(None)
        try:
            from app.core.cookie_config import ACCESS_TOKEN_COOKIE
            from app.core.security import verify_token

            auth_header = request.headers.get("Authorization", "")
            jwt_token = None
            if auth_header.startswith("Bearer "):
                jwt_token = auth_header[7:]
            if not jwt_token:
                jwt_token = request.cookies.get(ACCESS_TOKEN_COOKIE)
            if jwt_token:
                payload = verify_token(jwt_token)
                uid = payload.get("sub") or payload.get("user_id")
                if uid:
                    user_id_ctx.set(str(uid))
        except Exception:
            pass  # Anonymous request — no user_id needed

        # --- Process request ---
        start = time.monotonic()
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        finally:
            duration_ms = round((time.monotonic() - start) * 1000, 2)

            # Record Prometheus metric
            if _record_http is not None:
                try:
                    _record_http(request.method, request.url.path, status_code, duration_ms)
                except Exception:
                    pass  # Never let metrics break the request pipeline

            # Structured access log (skip noisy health probes)
            if request.url.path not in self.SKIP_PATHS:
                level = "WARNING" if status_code >= 400 else "INFO"
                logger.log(
                    __import__("logging").getLevelName(level),
                    f"http_request {request.method} {request.url.path} → {status_code}",
                    extra={"extra": {
                        "event_name": "http_request",
                        "event_category": "api",
                        "method": request.method,
                        "path": request.url.path,
                        "query": str(request.url.query) if request.url.query else None,
                        "status_code": status_code,
                        "execution_time_ms": duration_ms,
                        "user_agent": request.headers.get("user-agent"),
                        "client_ip": _get_client_ip(request),
                    }},
                )

            # Reset context vars
            request_id_ctx.reset(tok_rid)
            correlation_id_ctx.reset(tok_cid)
            trace_id_ctx.reset(tok_tid)
            session_id_ctx.reset(tok_sid)
            user_id_ctx.reset(tok_uid)

        # --- Attach trace headers to response ---
        response.headers["X-Request-ID"]     = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Trace-ID"]       = trace_id
        return response


def _get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
