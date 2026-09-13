"""
common_schemas.py — Standardised API response envelopes.

Every API response (success or error) is wrapped in a consistent envelope so
that clients can always rely on the same top-level structure.

Success envelope:
    {
        "success": true,
        "data": { ... },
        "meta": { "request_id": "...", "trace_id": "..." }
    }

Error envelope:
    {
        "success": false,
        "error": {
            "code": "LLM_PROVIDER_ERROR",
            "category": "external_service_error",
            "request_id": "req-...",
            "trace_id": "trace-...",
            "user_message": "...",
            "developer_message": "...",
            "recovery_suggestions": [...]
        }
    }
"""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


# ── Meta (always attached) ────────────────────────────────────────────────────

class ResponseMeta(BaseModel):
    """Metadata attached to every API response for traceability."""
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Error detail ──────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """Machine-readable error descriptor included in all error responses."""
    code: str                                    # ErrorCode enum value
    category: str                                # ErrorCategory enum value
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    user_message: str                            # Safe for end-user display
    developer_message: Optional[str] = None     # Internal context (omitted in prod)
    recovery_suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Response envelopes ────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error envelope returned by all failing API calls."""
    success: bool = False
    error: ErrorDetail

    # Keep backward-compat: expose top-level `detail` used by many existing routes
    @property
    def detail(self) -> str:
        return self.error.user_message


class SuccessResponse(BaseModel, Generic[DataT]):
    """Standard success envelope. Use `data` for the payload."""
    success: bool = True
    data: Optional[DataT] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class MessageResponse(BaseModel):
    """Lightweight success response carrying only a human message."""
    success: bool = True
    message: str
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    features: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Backward compatibility aliases ────────────────────────────────────────────
# The original ErrorResponse had `detail` + `status_code` fields.
# Existing routes that still construct ErrorResponse(...) directly will break
# if we remove those fields. Provide a factory function to ease migration.

def make_error_response(
    code: str,
    category: str,
    user_message: str,
    developer_message: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    recovery_suggestions: Optional[List[str]] = None,
) -> ErrorResponse:
    """Convenience factory for building a standard ErrorResponse."""
    return ErrorResponse(
        error=ErrorDetail(
            code=code,
            category=category,
            user_message=user_message,
            developer_message=developer_message,
            request_id=request_id,
            trace_id=trace_id,
            recovery_suggestions=recovery_suggestions or [],
        )
    )
