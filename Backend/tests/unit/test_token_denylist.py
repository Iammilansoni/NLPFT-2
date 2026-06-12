"""
Unit tests for JWT revocation (fix 1.3).

Covers:
- Access/refresh tokens carry unique `jti` claims
- revoke_token stores the jti with a TTL bounded by token expiry
- is_token_revoked detects revoked jtis
- Fail-open behavior when Redis is unavailable
- Legacy tokens without jti are not treated as revoked
"""

import time
from unittest.mock import AsyncMock, patch

import pytest

from app.core import token_denylist
from app.services.auth_service import AuthService


class TestJtiClaims:
    def test_access_token_has_unique_jti(self):
        t1 = AuthService.decode_token(AuthService.create_access_token({"sub": "u1"}))
        t2 = AuthService.decode_token(AuthService.create_access_token({"sub": "u1"}))
        assert t1["jti"] and t2["jti"]
        assert t1["jti"] != t2["jti"]
        assert t1["type"] == "access"

    def test_refresh_token_has_unique_jti(self):
        t1 = AuthService.decode_token(AuthService.create_refresh_token({"sub": "u1"}))
        t2 = AuthService.decode_token(AuthService.create_refresh_token({"sub": "u1"}))
        assert t1["jti"] and t2["jti"]
        assert t1["jti"] != t2["jti"]
        assert t1["type"] == "refresh"


@pytest.mark.asyncio
class TestDenylist:
    async def test_revoke_token_sets_key_with_ttl(self):
        client = AsyncMock()
        with patch.object(token_denylist, "_get_client", return_value=client):
            exp = int(time.time()) + 600
            ok = await token_denylist.revoke_token("abc-123", exp)
        assert ok is True
        args = client.setex.call_args[0]
        assert args[0] == f"{token_denylist.DENYLIST_PREFIX}abc-123"
        assert 1 <= args[1] <= 600  # TTL never exceeds remaining lifetime

    async def test_expired_token_gets_minimal_ttl(self):
        client = AsyncMock()
        with patch.object(token_denylist, "_get_client", return_value=client):
            ok = await token_denylist.revoke_token("abc-123", int(time.time()) - 100)
        assert ok is True
        assert client.setex.call_args[0][1] == 1

    async def test_revoked_jti_is_detected(self):
        client = AsyncMock()
        client.exists.return_value = 1
        with patch.object(token_denylist, "_get_client", return_value=client):
            assert await token_denylist.is_token_revoked("abc-123") is True

    async def test_unrevoked_jti_passes(self):
        client = AsyncMock()
        client.exists.return_value = 0
        with patch.object(token_denylist, "_get_client", return_value=client):
            assert await token_denylist.is_token_revoked("abc-123") is False

    async def test_missing_jti_is_not_revoked(self):
        # Legacy tokens (pre-jti) must not break auth
        assert await token_denylist.is_token_revoked(None) is False
        assert await token_denylist.is_token_revoked("") is False

    async def test_fail_open_on_redis_error(self):
        client = AsyncMock()
        client.exists.side_effect = ConnectionError("redis down")
        with patch.object(token_denylist, "_get_client", return_value=client):
            assert await token_denylist.is_token_revoked("abc-123") is False

    async def test_revoke_returns_false_on_redis_error(self):
        client = AsyncMock()
        client.setex.side_effect = ConnectionError("redis down")
        with patch.object(token_denylist, "_get_client", return_value=client):
            ok = await token_denylist.revoke_token("abc-123", int(time.time()) + 60)
        assert ok is False
