"""
UTC Datetime Utilities for NLPForge

Design Decision:
    PostgreSQL uses TIMESTAMP WITHOUT TIME ZONE columns throughout this project.
    SQLAlchemy stores timezone-naive datetimes in UTC by convention.
    The utc_now() function in database_models.py intentionally strips tzinfo
    to match this column type.

    However, some code paths (e.g., JWT expiry in python-jose) use
    datetime.now(timezone.utc) which produces timezone-aware datetimes.
    Comparing naive and aware datetimes raises TypeError in Python.

    These helpers standardize datetime handling:
    - utc_now_naive(): For database columns (TIMESTAMP WITHOUT TIME ZONE)
    - utc_now_aware(): For JWT, external APIs, and comparisons with aware datetimes
    - to_naive_utc(): Convert any datetime to naive UTC for database storage
"""

from datetime import datetime, timezone


def utc_now_naive() -> datetime:
    """Return current UTC time as timezone-naive datetime.

    Use for PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns.
    Equivalent to database_models.utc_now().
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_now_aware() -> datetime:
    """Return current UTC time as timezone-aware datetime.

    Use for JWT tokens, external API calls, and any comparison
    with timezone-aware datetimes.
    """
    return datetime.now(timezone.utc)


def to_naive_utc(dt: datetime) -> datetime:
    """Convert a datetime to naive UTC for database storage.

    If the datetime is timezone-aware, converts to UTC and strips tzinfo.
    If already naive, assumes it's already in UTC and returns as-is.

    Args:
        dt: A datetime object (naive or aware).

    Returns:
        A timezone-naive datetime in UTC.
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
        return dt.replace(tzinfo=None)
    return dt
