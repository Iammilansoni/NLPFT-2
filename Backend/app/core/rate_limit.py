"""
Shared rate limiter.

One Limiter for the whole app, so every decorated route counts against the same
store:

  * Redis-backed when Redis is reachable, so limits hold across uvicorn workers
    and replicas instead of multiplying by the worker count.
  * Falls back to in-process memory (and never 500s) if Redis goes away.
  * Keys on the real client address. Browser traffic arrives through the Next.js
    proxy, so the TCP peer is the frontend container for every user; the
    X-Forwarded-For header is honoured only when that peer is a trusted proxy
    (private network by default), so a public client cannot spoof its key.
"""

from __future__ import annotations

import ipaddress
import os
from typing import List

from slowapi import Limiter
from starlette.requests import Request

from app.core.config import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT

_DEFAULT_TRUSTED = "127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,::1/128"
_TRUSTED: List[ipaddress._BaseNetwork] = [
    ipaddress.ip_network(c.strip(), strict=False)
    for c in os.getenv("TRUSTED_PROXY_CIDRS", _DEFAULT_TRUSTED).split(",")
    if c.strip()
]


def _is_trusted(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(ip in net for net in _TRUSTED)


def client_key(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded and _is_trusted(peer):
        return forwarded.split(",")[0].strip() or peer
    return peer


def _storage_uri() -> str:
    auth = f":{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""
    return f"redis://{auth}{REDIS_HOST}:{REDIS_PORT}/3"


limiter = Limiter(
    key_func=client_key,
    storage_uri=_storage_uri(),
    in_memory_fallback_enabled=True,
    swallow_errors=True,
    headers_enabled=False,
)
