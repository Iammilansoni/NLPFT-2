"""
exceptions.py — NLPForge standardised exception hierarchy & error registry.

DESIGN PRINCIPLES
-----------------
1.  Every non-200 response has a machine-readable error code.
2.  Each exception maps to: HTTP status, user message, developer message.
3.  The global FastAPI exception handler in main.py maps Python exceptions
    to these types before serialising.

HIERARCHY
---------
NLPForgeError (base)
├── ValidationError         400
├── AuthenticationError     401
├── AuthorizationError      403
├── NotFoundError           404
├── ConflictError           409
├── RateLimitError          429
├── ExternalServiceError    502
│   ├── LLMProviderError
│   ├── EmbeddingProviderError
│   └── EmailServiceError
├── ServiceUnavailableError 503
│   ├── DatabaseError
│   └── RedisError
└── InternalError           500
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Optional

# ── Error codes ───────────────────────────────────────────────────────────────

class ErrorCode(str, Enum):
    # Validation
    VALIDATION_FAILED          = "VALIDATION_FAILED"
    INVALID_INPUT              = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD     = "MISSING_REQUIRED_FIELD"

    # Authentication
    INVALID_CREDENTIALS        = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED              = "TOKEN_EXPIRED"
    TOKEN_INVALID              = "TOKEN_INVALID"
    TOKEN_REVOKED              = "TOKEN_REVOKED"
    EMAIL_NOT_VERIFIED         = "EMAIL_NOT_VERIFIED"
    ACCOUNT_INACTIVE           = "ACCOUNT_INACTIVE"

    # Authorization
    PERMISSION_DENIED          = "PERMISSION_DENIED"
    EXPERT_ONLY                = "EXPERT_ONLY"
    ADMIN_ONLY                 = "ADMIN_ONLY"

    # Not found
    RESOURCE_NOT_FOUND         = "RESOURCE_NOT_FOUND"
    USER_NOT_FOUND             = "USER_NOT_FOUND"
    TEMPLATE_NOT_FOUND         = "TEMPLATE_NOT_FOUND"
    DATASET_NOT_FOUND          = "DATASET_NOT_FOUND"
    MODEL_NOT_FOUND            = "MODEL_NOT_FOUND"

    # Conflict / Business Logic
    RESOURCE_ALREADY_EXISTS    = "RESOURCE_ALREADY_EXISTS"
    EMAIL_ALREADY_REGISTERED   = "EMAIL_ALREADY_REGISTERED"
    TASK_ALREADY_RUNNING       = "TASK_ALREADY_RUNNING"
    DATASET_GENERATION_RUNNING = "DATASET_GENERATION_RUNNING"
    EMBEDDING_ALREADY_EXISTS   = "EMBEDDING_ALREADY_EXISTS"

    # Rate limiting
    RATE_LIMIT_EXCEEDED        = "RATE_LIMIT_EXCEEDED"

    # External services
    LLM_PROVIDER_ERROR         = "LLM_PROVIDER_ERROR"
    LLM_RATE_LIMIT_EXCEEDED    = "LLM_RATE_LIMIT_EXCEEDED"
    LLM_CONTEXT_TOO_LONG       = "LLM_CONTEXT_TOO_LONG"
    LLM_INVALID_API_KEY        = "LLM_INVALID_API_KEY"
    EMBEDDING_PROVIDER_ERROR   = "EMBEDDING_PROVIDER_ERROR"
    EMBEDDING_MODEL_NOT_LOADED = "EMBEDDING_MODEL_NOT_LOADED"
    EMAIL_DELIVERY_FAILED      = "EMAIL_DELIVERY_FAILED"
    EMAIL_NOT_CONFIGURED       = "EMAIL_NOT_CONFIGURED"
    RERANKER_ERROR             = "RERANKER_ERROR"

    # Infrastructure
    DATABASE_ERROR             = "DATABASE_ERROR"
    DATABASE_UNAVAILABLE       = "DATABASE_UNAVAILABLE"
    REDIS_ERROR                = "REDIS_ERROR"
    REDIS_UNAVAILABLE          = "REDIS_UNAVAILABLE"
    VECTOR_SEARCH_ERROR        = "VECTOR_SEARCH_ERROR"
    FILE_UPLOAD_ERROR          = "FILE_UPLOAD_ERROR"
    EXPORT_ERROR               = "EXPORT_ERROR"

    # Generic
    INTERNAL_ERROR             = "INTERNAL_ERROR"
    FEATURE_UNAVAILABLE        = "FEATURE_UNAVAILABLE"
    CONFIGURATION_ERROR        = "CONFIGURATION_ERROR"


# ── Category strings ──────────────────────────────────────────────────────────

class ErrorCategory(str, Enum):
    VALIDATION     = "validation_error"
    AUTHENTICATION = "authentication_error"
    AUTHORIZATION  = "authorization_error"
    NOT_FOUND      = "not_found"
    CONFLICT       = "conflict"
    RATE_LIMIT     = "rate_limit"
    EXTERNAL       = "external_service_error"
    INFRASTRUCTURE = "infrastructure_error"
    INTERNAL       = "internal_error"


# ── Base exception ────────────────────────────────────────────────────────────

class NLPForgeError(Exception):
    """
    Base class for all application-controlled exceptions.

    Attributes:
        code:           Machine-readable error code (from ErrorCode enum).
        category:       Error category (from ErrorCategory enum).
        http_status:    HTTP status code to use in the response.
        user_message:   Safe message shown to end users (no stack traces).
        developer_message: Detailed message for developers / logs (may contain
                         internal context but NEVER secrets).
        recovery_suggestions: Optional list of hints shown in the API response.
        extra:          Arbitrary key-value context attached to the structured log.
    """

    http_status: int = 500
    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    category: ErrorCategory = ErrorCategory.INTERNAL

    def __init__(
        self,
        user_message: str = "An unexpected error occurred.",
        developer_message: Optional[str] = None,
        *,
        code: Optional[ErrorCode] = None,
        recovery_suggestions: Optional[list[str]] = None,
        extra: Optional[dict[str, Any]] = None,
    ):
        super().__init__(developer_message or user_message)
        self.user_message = user_message
        self.developer_message = developer_message or user_message
        if code is not None:
            self.code = code
        self.recovery_suggestions = recovery_suggestions or []
        self.extra = extra or {}


# ── Concrete exception types ──────────────────────────────────────────────────

class ValidationError(NLPForgeError):
    http_status = 400
    code = ErrorCode.VALIDATION_FAILED
    category = ErrorCategory.VALIDATION


class AuthenticationError(NLPForgeError):
    http_status = 401
    code = ErrorCode.INVALID_CREDENTIALS
    category = ErrorCategory.AUTHENTICATION


class TokenExpiredError(AuthenticationError):
    code = ErrorCode.TOKEN_EXPIRED

    def __init__(self, **kwargs):
        super().__init__(
            user_message="Your session has expired. Please log in again.",
            recovery_suggestions=["Refresh your access token", "Log in again"],
            **kwargs,
        )


class TokenInvalidError(AuthenticationError):
    code = ErrorCode.TOKEN_INVALID

    def __init__(self, **kwargs):
        super().__init__(
            user_message="Invalid or malformed authentication token.",
            **kwargs,
        )


class AuthorizationError(NLPForgeError):
    http_status = 403
    code = ErrorCode.PERMISSION_DENIED
    category = ErrorCategory.AUTHORIZATION


class NotFoundError(NLPForgeError):
    http_status = 404
    code = ErrorCode.RESOURCE_NOT_FOUND
    category = ErrorCategory.NOT_FOUND


class ConflictError(NLPForgeError):
    http_status = 409
    code = ErrorCode.RESOURCE_ALREADY_EXISTS
    category = ErrorCategory.CONFLICT


class RateLimitError(NLPForgeError):
    http_status = 429
    code = ErrorCode.RATE_LIMIT_EXCEEDED
    category = ErrorCategory.RATE_LIMIT

    def __init__(self, **kwargs):
        super().__init__(
            user_message="Too many requests. Please slow down.",
            recovery_suggestions=["Wait before retrying", "Reduce request frequency"],
            **kwargs,
        )


class ExternalServiceError(NLPForgeError):
    http_status = 502
    code = ErrorCode.INTERNAL_ERROR
    category = ErrorCategory.EXTERNAL


class LLMProviderError(ExternalServiceError):
    code = ErrorCode.LLM_PROVIDER_ERROR

    def __init__(
        self,
        provider: str,
        detail: str = "",
        *,
        rate_limited: bool = False,
        **kwargs,
    ):
        code = ErrorCode.LLM_RATE_LIMIT_EXCEEDED if rate_limited else ErrorCode.LLM_PROVIDER_ERROR
        super().__init__(
            user_message="The AI provider is currently unavailable. Please try again shortly.",
            developer_message=f"LLM provider '{provider}' error: {detail}",
            code=code,
            recovery_suggestions=[
                "Retry in a few seconds",
                "Switch to a different LLM provider in Settings",
            ],
            **kwargs,
        )


class EmbeddingProviderError(ExternalServiceError):
    code = ErrorCode.EMBEDDING_PROVIDER_ERROR

    def __init__(self, model: str, detail: str = "", **kwargs):
        super().__init__(
            user_message="The embedding model is unavailable. Vector search may be degraded.",
            developer_message=f"Embedding model '{model}' error: {detail}",
            **kwargs,
        )


class EmailServiceError(ExternalServiceError):
    code = ErrorCode.EMAIL_DELIVERY_FAILED

    def __init__(self, detail: str = "", **kwargs):
        super().__init__(
            user_message="We could not send the email at this time. Please try again later.",
            developer_message=f"Email delivery error: {detail}",
            **kwargs,
        )


class ServiceUnavailableError(NLPForgeError):
    http_status = 503
    category = ErrorCategory.INFRASTRUCTURE


class DatabaseError(ServiceUnavailableError):
    code = ErrorCode.DATABASE_UNAVAILABLE

    def __init__(self, detail: str = "", **kwargs):
        super().__init__(
            user_message="A database error occurred. Please try again shortly.",
            developer_message=f"Database error: {detail}",
            recovery_suggestions=["Check PostgreSQL health", "Retry in a few seconds"],
            **kwargs,
        )


class RedisError(ServiceUnavailableError):
    code = ErrorCode.REDIS_UNAVAILABLE

    def __init__(self, detail: str = "", **kwargs):
        super().__init__(
            user_message="A cache/search service error occurred. Some features may be unavailable.",
            developer_message=f"Redis error: {detail}",
            **kwargs,
        )


class VectorSearchError(ServiceUnavailableError):
    code = ErrorCode.VECTOR_SEARCH_ERROR


class InternalError(NLPForgeError):
    http_status = 500
    code = ErrorCode.INTERNAL_ERROR
    category = ErrorCategory.INTERNAL


class ConfigurationError(InternalError):
    code = ErrorCode.CONFIGURATION_ERROR

    def __init__(self, setting: str, **kwargs):
        super().__init__(
            user_message="The service is not properly configured. Please contact support.",
            developer_message=f"Missing or invalid configuration: {setting}",
            **kwargs,
        )


class TaskAlreadyRunningError(ConflictError):
    code = ErrorCode.TASK_ALREADY_RUNNING

    def __init__(self, task_name: str = "task", **kwargs):
        super().__init__(
            user_message=f"A {task_name} is already in progress. Please wait for it to complete.",
            recovery_suggestions=["Wait for the current task to finish", "Cancel the running task first"],
            **kwargs,
        )
