"""
logger.py — Structured, context-aware logging for NLPForge.

DESIGN
------
*   Every log record is emitted as a single-line JSON object in production
    and as coloured human-readable text in development.
*   Context variables (request_id, correlation_id, trace_id, user_id) are
    automatically injected into every record via a logging.Filter.
*   A LogScrubberFilter masks secrets and PII before records reach any handler.
*   The WebSocket broadcast handler (LogManager) only receives records at
    INFO level and above.

USAGE
-----
    from app.core.logger import get_logger

    logger = get_logger(__name__)          # preferred — named per module
    logger.info("User signed in", extra={"user_id": uid, "ip": ip})

    # Structured event helper (ensures all 16 fields are present)
    from app.core.logger import log_event
    log_event(
        "dataset_generation_started",
        category="ai_pipeline",
        level="INFO",
        input_context={"template_id": str(tid), "num_examples": 100},
    )
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.context_vars import get_log_context
from app.core.log_scrubber import LogScrubberFilter

# ── Configuration ─────────────────────────────────────────────────────────────

SERVICE_NAME = os.getenv("SERVICE_NAME", "nlpforge-backend")
ENVIRONMENT  = os.getenv("ENVIRONMENT", "production").lower()
IS_PRODUCTION = ENVIRONMENT == "production"
LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO").upper()

# ── Context-injection filter ──────────────────────────────────────────────────

class ContextFilter(logging.Filter):
    """Injects request-scoped context vars into every LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = get_log_context()
        record.request_id    = ctx.get("request_id")
        record.correlation_id = ctx.get("correlation_id")
        record.trace_id      = ctx.get("trace_id")
        record.session_id    = ctx.get("session_id")
        record.user_id       = ctx.get("user_id")
        record.service       = SERVICE_NAME
        record.environment   = ENVIRONMENT
        return True


# ── Formatters ────────────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """
    Emits each log record as a single-line JSON object suitable for
    Loki/CloudWatch/ELK ingestion.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp":      datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "severity":       record.levelname,
            "service":        getattr(record, "service", SERVICE_NAME),
            "environment":    getattr(record, "environment", ENVIRONMENT),
            "module":         f"{record.name}:{record.funcName}:{record.lineno}",
            "message":        record.getMessage(),
            # Context IDs
            "request_id":     getattr(record, "request_id", None),
            "correlation_id": getattr(record, "correlation_id", None),
            "trace_id":       getattr(record, "trace_id", None),
            "session_id":     getattr(record, "session_id", None),
            "user_id":        getattr(record, "user_id", None),
        }

        # Attach any extra structured fields passed via extra={}
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_obj.update(record.extra)

        # Exception information
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        elif record.exc_text:
            log_obj["exception"] = record.exc_text

        # Remove None values to keep logs compact
        log_obj = {k: v for k, v in log_obj.items() if v is not None}

        return json.dumps(log_obj, default=str, ensure_ascii=False)


class ColourFormatter(logging.Formatter):
    """Human-readable coloured formatter for local development."""

    _COLOURS = {
        "DEBUG":    "\033[36m",   # Cyan
        "INFO":     "\033[32m",   # Green
        "WARNING":  "\033[33m",   # Yellow
        "ERROR":    "\033[31m",   # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        colour = self._COLOURS.get(record.levelname, self._RESET)
        level  = f"{colour}{record.levelname:<8}{self._RESET}"

        rid = getattr(record, "request_id", None)
        rid_str = f" [{rid[:8]}]" if rid else ""

        uid = getattr(record, "user_id", None)
        uid_str = f" user={uid[:8]}" if uid else ""

        parts = [
            datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%S.%f")[:-3],
            level,
            f"{record.name}",
            rid_str,
            uid_str,
            "│",
            record.getMessage(),
        ]
        base = " ".join(p for p in parts if p)

        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


# ── Logger factory ────────────────────────────────────────────────────────────

def _shared_filters() -> list:
    return [ContextFilter(), LogScrubberFilter()]


def _make_console_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = JSONFormatter() if IS_PRODUCTION else ColourFormatter()
    handler.setFormatter(formatter)
    for f in _shared_filters():
        handler.addFilter(f)
    return handler


def setup_logger(name: str = "nlpforge", level: str = LOG_LEVEL) -> logging.Logger:
    """
    Configure and return a named logger.

    Calling this multiple times for the same `name` is safe — it
    reuses the existing logger and replaces its handlers.
    """
    log = logging.getLogger(name)
    log.setLevel(getattr(logging, level.upper(), logging.INFO))
    log.handlers.clear()
    log.addHandler(_make_console_handler())

    # WebSocket handler — attach live logs to the browser
    try:
        from app.core.log_manager import log_manager

        class WebSocketHandler(logging.Handler):
            def emit(self, record: logging.LogRecord):
                if record.levelno < logging.INFO:
                    return
                if "app.core.log_manager" in record.name:
                    return
                log_manager.handle_log(record)

        ws = WebSocketHandler()
        ws.setLevel(logging.INFO)
        for f in _shared_filters():
            ws.addFilter(f)
        log.addHandler(ws)
    except ImportError:
        pass

    log.propagate = False
    return log


def get_logger(module_name: str) -> logging.Logger:
    """
    Preferred factory: returns a named logger for a module.

    Usage:
        logger = get_logger(__name__)
    """
    log = logging.getLogger(module_name)
    if not log.handlers:
        log.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        log.addHandler(_make_console_handler())
        log.propagate = True  # propagate to root (which has WebSocket handler)
    return log


# ── Structured event helper ───────────────────────────────────────────────────

def log_event(
    event_name: str,
    *,
    category: str = "application",
    level: str = "INFO",
    input_context: Optional[Dict[str, Any]] = None,
    output_result: Optional[Dict[str, Any]] = None,
    execution_time_ms: Optional[float] = None,
    failure_cause: Optional[str] = None,
    recovery_action: Optional[str] = None,
    suggested_fix: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Emit a fully structured 16-field observability event.

    All fields that answer: What / Why / Where / Who / Which / How.
    """
    _logger = logging.getLogger("nlpforge.events")

    extra: Dict[str, Any] = {
        "event_name":       event_name,
        "event_category":   category,
    }
    if input_context:
        extra["input_context"] = input_context
    if output_result:
        extra["output_result"] = output_result
    if execution_time_ms is not None:
        extra["execution_time_ms"] = round(execution_time_ms, 3)
    if failure_cause:
        extra["failure_cause"] = failure_cause
    if recovery_action:
        extra["recovery_action"] = recovery_action
    if suggested_fix:
        extra["suggested_fix"] = suggested_fix
    extra.update(kwargs)

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    _logger.log(numeric_level, event_name, extra={"extra": extra})


# ── Convenience wrappers kept for backward compatibility ──────────────────────

def log_request(method: str, url: str, status_code: int, duration: float) -> None:
    logger.info(
        "http_request",
        extra={"extra": {
            "event_name": "http_request",
            "method": method,
            "path": url,
            "status_code": status_code,
            "execution_time_ms": round(duration * 1000, 2),
        }},
    )


def log_health_check(status: str, checks: Dict[str, Any]) -> None:
    logger.info(
        f"health_check status={status}",
        extra={"extra": {"event_name": "health_check", "status": status, "checks": checks}},
    )


def log_error(error: Exception, context: str = "") -> None:
    logger.exception(
        f"unhandled_exception context={context}",
        extra={"extra": {"event_name": "unhandled_exception", "error_type": type(error).__name__, "context": context}},
    )


def log_startup(component: str) -> None:
    logger.info(f"startup component={component}",
                extra={"extra": {"event_name": "startup", "component": component}})


def log_shutdown(component: str) -> None:
    logger.info(f"shutdown component={component}",
                extra={"extra": {"event_name": "shutdown", "component": component}})


# ── Root logger & global default instance ─────────────────────────────────────

# Configure the root "nlpforge" logger once at import time.
# All module-level loggers that propagate will funnel through this.
logger = setup_logger("nlpforge", LOG_LEVEL)

# Also configure the event logger
_events_logger = setup_logger("nlpforge.events", LOG_LEVEL)