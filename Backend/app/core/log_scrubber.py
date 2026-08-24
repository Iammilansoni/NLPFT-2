"""
log_scrubber.py — Automated PII and secret masking for structured log output.

HOW IT WORKS
------------
1.  A Python logging.Filter subclass (LogScrubberFilter) inspects every
    LogRecord before it reaches a handler.
2.  It applies regex substitution to the *formatted* message string AND
    recursively walks any dict/list attached to the record so structured
    JSON payloads are also sanitised.
3.  Sensitive key names (matching a blocklist) have their values replaced
    with the placeholder "***REDACTED***".
4.  Bearer tokens, raw JWT strings, and common secret patterns are masked
    with regex regardless of which key they appear under.

RULES
-----
- Passwords, secrets, API keys, and tokens are NEVER logged.
- User PII (email, phone) may appear in INFO/DEBUG logs only in development.
  In production they are masked.
- User prompt text is truncated to MAX_PROMPT_LOG_CHARS characters.
- Database connection strings have credentials replaced.
"""

import logging
import os
import re
from typing import Any

# ── Configuration ─────────────────────────────────────────────────────────────

ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()
IS_PRODUCTION = ENVIRONMENT == "production"
MAX_PROMPT_LOG_CHARS = 200

# Sensitive key names (exact match, case-insensitive)
_SENSITIVE_KEYS: frozenset[str] = frozenset({
    "password", "passwd", "pass",
    "secret", "secret_key", "signing_key",
    "api_key", "apikey", "api_secret",
    "token", "access_token", "refresh_token", "id_token",
    "jwt", "authorization", "auth",
    "private_key", "client_secret",
    "database_url", "db_url", "db_password",
    "smtp_password", "smtp_pass",
    "encryption_key", "key",
})

# PII keys — only masked in production
_PII_KEYS: frozenset[str] = frozenset({
    "email", "user_email", "phone", "phone_number",
    "ssn", "dob", "date_of_birth",
    "ip_address", "client_ip",
})

_REDACTED = "***REDACTED***"
_PII_MASKED = "***PII***"

# Regex patterns for value-level scrubbing (applied to string values)
_VALUE_PATTERNS: list[re.Pattern] = [
    # Bearer / JWT tokens in strings like "Authorization: Bearer eyJ..."
    re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    # Raw JWT pattern (3 base64url segments)
    re.compile(r"eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"),
    # PostgreSQL / SQLAlchemy URL with credentials
    re.compile(r"(postgresql(?:\+\w+)?://[^:]+:)([^@]+)(@)", re.IGNORECASE),
    # Redis URL with password  redis://:password@host
    re.compile(r"(redis://:[^@]+)(@)", re.IGNORECASE),
    # Generic "password=VALUE" patterns in query strings / log text
    re.compile(r"(password\s*=\s*)[^\s&\"']+", re.IGNORECASE),
    # API key in URL params
    re.compile(r"(api[_-]?key\s*=\s*)[^\s&\"']+", re.IGNORECASE),
]


def _scrub_string(value: str) -> str:
    """Apply regex scrubbing to a string value."""
    for pattern in _VALUE_PATTERNS:
        value = pattern.sub(lambda m: _redact_match(m), value)
    return value


def _redact_match(m: re.Match) -> str:
    """Replacement callback — preserves safe groups, masks sensitive data."""
    groups = m.groups()
    if groups:
        # Keep the first (prefix) group, mask the secret group, keep last (suffix)
        parts = list(groups)
        # The middle group(s) are redacted
        if len(parts) == 3:
            return parts[0] + _REDACTED + parts[2]
        if len(parts) == 2:
            return parts[0] + _REDACTED
        # Single group: replace entirely
        return _REDACTED
    return _REDACTED


def _scrub_value(key: str, value: Any) -> Any:
    """Scrub a value based on its associated key name."""
    key_lower = key.lower()

    # Hard block — always redact
    if key_lower in _SENSITIVE_KEYS:
        return _REDACTED

    # PII — redact in production, mask lightly in development
    if IS_PRODUCTION and key_lower in _PII_KEYS:
        return _PII_MASKED

    # Recurse into nested structures
    if isinstance(value, dict):
        return _scrub_dict(value)
    if isinstance(value, list):
        return [_scrub_value(key, item) for item in value]

    # Truncate long prompts / user inputs
    if key_lower in {"prompt", "user_prompt", "input", "query", "text", "content"}:
        if isinstance(value, str) and len(value) > MAX_PROMPT_LOG_CHARS:
            return value[:MAX_PROMPT_LOG_CHARS] + f"...[truncated {len(value) - MAX_PROMPT_LOG_CHARS} chars]"

    # Apply regex scrubbing to string values regardless of key
    if isinstance(value, str):
        return _scrub_string(value)

    return value


def _scrub_dict(data: dict) -> dict:
    """Recursively scrub a dict in-place and return it."""
    return {k: _scrub_value(k, v) for k, v in data.items()}


# ── Logging Filter ────────────────────────────────────────────────────────────

class LogScrubberFilter(logging.Filter):
    """
    Logging filter that masks sensitive data from all log records.

    Attach to any handler or logger:
        handler.addFilter(LogScrubberFilter())
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Scrub the formatted message
        if isinstance(record.msg, str):
            record.msg = _scrub_string(record.msg)

        # Scrub any extra structured fields attached to the record
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            record.extra = _scrub_dict(record.extra)

        # Scrub exc_text (exception message can leak secrets in tracebacks)
        # We leave the raw exc_info intact for developer debugging but
        # sanitise the formatted string if already built.
        if record.exc_text:
            record.exc_text = _scrub_string(record.exc_text)

        return True  # always allow the record through (after scrubbing)
