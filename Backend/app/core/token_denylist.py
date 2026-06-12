"""
JWT Token Denylist - Redis-backed token revocation

Enables true logout for stateless JWTs: every token carries a unique `jti`
claim; on logout (or refresh rotation) the jti is pushed to Redis with a
TTL equal to the token's remaining lifetime. Auth checks reject any token
whose jti is present in the denylist.

Memory is bounded: entries expire automatically when the token itself
would have expired, so the denylist only ever holds live revoked tokens.

AVAILABILITY TRADE-OFF: if Redis is unreachable, revocation checks
fail-open (token accepted) so an infra outage does not lock every user
out. Failures are logged loudly. Redis is a core dependency of this app
(vector store), so in practice an outage here is already fatal elsewhere.
"""

import time
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from app.core.logger import logger

DENYLIST_PREFIX = "auth:denylist:"

_client: Optional[aioredis.Redis] = None


def _get_client() -> aioredis.Redis:
    """Lazily create a shared async Redis client."""
    global _client
    if _client is None:
        _client = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD or None,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client


async def revoke_token(jti: str, exp: int) -> bool:
    """
    Add a token's jti to the denylist until its natural expiry.

    Args:
        jti: Unique token identifier (uuid4 string from the `jti` claim).
        exp: Token expiry as a unix timestamp (the `exp` claim).

    Returns:
        True if the revocation was recorded, False on failure.
    """
    if not jti:
        return False
    ttl = max(int(exp - time.time()), 1)
    try:
        await _get_client().setex(f"{DENYLIST_PREFIX}{jti}", ttl, "1")
        return True
    except Exception as e:
        logger.error(f"TOKEN DENYLIST UNAVAILABLE - could not revoke jti={jti}: {e}")
        return False


async def is_token_revoked(jti: Optional[str]) -> bool:
    """
    Check whether a token's jti has been revoked.

    Tokens without a jti (issued before this feature) are treated as
    not revoked; they will age out within the access-token lifetime.
    """
    if not jti:
        return False
    try:
        return await _get_client().exists(f"{DENYLIST_PREFIX}{jti}") == 1
    except Exception as e:
        logger.error(f"TOKEN DENYLIST UNAVAILABLE - failing open for jti={jti}: {e}")
        return False
