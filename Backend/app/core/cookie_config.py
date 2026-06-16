"""
cookie_config.py — Centralised HttpOnly cookie configuration

All auth cookie parameters live here so they are consistent across
login, refresh, logout, and get_current_user.
"""

import os

# ── Cookie names ──────────────────────────────────────────────────────────────
ACCESS_TOKEN_COOKIE  = "nlpf_access"
REFRESH_TOKEN_COOKIE = "nlpf_refresh"

# ── Lifetimes (seconds) ───────────────────────────────────────────────────────
ACCESS_TOKEN_MAX_AGE  = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")) * 60
REFRESH_TOKEN_MAX_AGE = 60 * 60 * 24 * 7   # 7 days

# ── Security flags ────────────────────────────────────────────────────────────
_env = os.getenv("ENVIRONMENT", "development")
COOKIE_SECURE   = _env == "production"   # Requires HTTPS in production
COOKIE_SAMESITE = "lax"                  # Lax: protects CSRF, allows top-level nav


def set_auth_cookies(response, access_token: str, refresh_token: str) -> None:
    """Attach both auth cookies to a FastAPI Response object."""
    _common = dict(httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE, path="/")

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        max_age=ACCESS_TOKEN_MAX_AGE,
        **_common,
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=REFRESH_TOKEN_MAX_AGE,
        path="/api/v1/auth/refresh",   # Scope refresh cookie to refresh endpoint only
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )


def clear_auth_cookies(response) -> None:
    """Expire both auth cookies."""
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE,  path="/")
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/api/v1/auth/refresh")
