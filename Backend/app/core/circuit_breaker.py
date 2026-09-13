"""
Distributed Circuit Breaker
===========================

Protects calls to flaky external dependencies (Ollama, hosted LLM APIs) by
failing fast once a dependency is demonstrably down, instead of letting every
request pile up against a dead socket until it times out.

WHY REDIS AND NOT AN IN-PROCESS BREAKER
---------------------------------------
NLPForge runs the FastAPI app and N Celery workers as separate processes
(docker-compose.yml:69 and :174). A library like `pybreaker` keeps state in
process memory, which means the API could correctly trip its breaker while three
workers keep hammering the same dead Ollama - each maintaining its own private,
useless view of the dependency's health.

Breaker state is a property of the DEPENDENCY, not of the process observing it.
So it lives in Redis, shared by every process.

STATES
------
    CLOSED     Normal. Calls pass through. Failures increment a windowed counter.
    OPEN       Tripped. Calls fail immediately with CircuitOpenError. Set with a
               TTL equal to recovery_timeout, so the key expiring IS the
               transition to HALF_OPEN - no background timer needed.
    HALF_OPEN  Probation. Exactly one probe call is admitted (guarded by a
               SET NX token). Success closes the circuit; failure re-opens it.

FAIL-OPEN ON THE BREAKER ITSELF
-------------------------------
If Redis is unreachable, this breaker allows the call through rather than
blocking it. A monitoring component must never become the outage. Redis failure
is logged, not raised.

USAGE
-----
    breaker = get_breaker("ollama_extraction")
    try:
        result = await breaker.call(client.post, url, json=payload)
    except CircuitOpenError:
        return degraded_response()
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from app.core.logger import logger

T = TypeVar("T")

DEFAULT_FAILURE_THRESHOLD = int(os.getenv("CB_FAILURE_THRESHOLD", "5"))
DEFAULT_RECOVERY_TIMEOUT = int(os.getenv("CB_RECOVERY_TIMEOUT", "30"))
DEFAULT_WINDOW_SECONDS = int(os.getenv("CB_WINDOW_SECONDS", "60"))


class BreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised instead of attempting a call while the circuit is open."""

    def __init__(self, name: str, retry_after: float):
        self.name = name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit '{name}' is OPEN; retry in ~{retry_after:.0f}s"
        )


@dataclass
class BreakerStats:
    name: str
    state: BreakerState
    failures: int
    retry_after: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failures,
            "retry_after_s": round(self.retry_after, 1),
        }


# ---------------------------------------------------------------------------
# Atomic admission check
# ---------------------------------------------------------------------------
# Executed server-side so the OPEN check and the HALF_OPEN probe-token
# acquisition cannot interleave between processes. Without this, N workers
# hitting an expiring OPEN key would all believe they own the single probe.
#
# THREE keys are required, not two. The `open` key alone cannot distinguish
# "never tripped" from "tripped and the block window just expired" - both look
# like a missing key. Conflating them let the first call after opening walk
# straight through as a probe, so tripping the breaker blocked nothing.
#
#   KEYS[1] open     TTL = recovery_timeout. Present => reject outright.
#   KEYS[2] tripped  TTL = recovery_timeout * 3. Outlives `open`, so its presence
#                    after `open` expires is what marks HALF_OPEN.
#   KEYS[3] probe    SET NX token admitting exactly one probe call.
#
#   ARGV[1] = probe token TTL
#
# Returns: {allowed(0|1), state_string, ttl_remaining}
_ADMIT_LUA = """
if redis.call('EXISTS', KEYS[1]) == 1 then
  return {0, 'open', redis.call('TTL', KEYS[1])}
end
if redis.call('EXISTS', KEYS[2]) == 1 then
  if redis.call('SET', KEYS[3], '1', 'NX', 'EX', ARGV[1]) then
    return {1, 'half_open', 0}
  end
  return {0, 'open', 1}
end
return {1, 'closed', 0}
"""


class CircuitBreaker:
    """One breaker per named dependency. Safe to construct per call site."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        recovery_timeout: int = DEFAULT_RECOVERY_TIMEOUT,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        redis_client: Any = None,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.window_seconds = window_seconds
        self._redis = redis_client
        self._admit_script: Any = None
        # Last-resort local state, used only when Redis is unreachable so a
        # single process still gets some protection.
        self._local_failures = 0
        self._local_open_until = 0.0

    # -- keys ---------------------------------------------------------------

    @property
    def _k_state(self) -> str:
        """Present => hard reject. TTL is the block window."""
        return f"cb:{self.name}:open"

    @property
    def _k_tripped(self) -> str:
        """Outlives _k_state; its presence after that expires means HALF_OPEN."""
        return f"cb:{self.name}:tripped"

    @property
    def _k_failures(self) -> str:
        return f"cb:{self.name}:failures"

    @property
    def _k_probe(self) -> str:
        return f"cb:{self.name}:probe"

    # -- redis plumbing -----------------------------------------------------

    def _client(self) -> Any:
        if self._redis is None:
            try:
                from app.services.multi_model_redis_service import (
                    get_multi_model_redis_service,
                )

                self._redis = get_multi_model_redis_service().redis_client
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"Circuit breaker '{self.name}': no Redis ({exc})")
                return None
        return self._redis

    # -- state --------------------------------------------------------------

    async def _admit(self) -> tuple[bool, BreakerState, float]:
        """Decide whether this call may proceed. Fails open if Redis is down."""
        client = self._client()
        if client is None:
            now = time.monotonic()
            if now < self._local_open_until:
                return False, BreakerState.OPEN, self._local_open_until - now
            return True, BreakerState.CLOSED, 0.0

        try:
            if self._admit_script is None:
                self._admit_script = client.register_script(_ADMIT_LUA)
            allowed, state, ttl = await asyncio.to_thread(
                self._admit_script,
                keys=[self._k_state, self._k_tripped, self._k_probe],
                args=[max(1, self.recovery_timeout // 2)],
            )
            state_str = state.decode() if isinstance(state, bytes) else str(state)
            return bool(int(allowed)), BreakerState(state_str), float(ttl or 0)
        except Exception as exc:  # noqa: BLE001 - never let monitoring cause an outage
            logger.warning(f"Circuit breaker '{self.name}': Redis check failed ({exc}); failing open")
            return True, BreakerState.CLOSED, 0.0

    async def _record_success(self) -> None:
        client = self._client()
        self._local_failures = 0
        self._local_open_until = 0.0
        if client is None:
            return
        try:
            await asyncio.to_thread(
                client.delete,
                self._k_state,
                self._k_tripped,
                self._k_failures,
                self._k_probe,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Circuit breaker '{self.name}': success reset failed ({exc})")

    async def _record_failure(self) -> None:
        client = self._client()
        if client is None:
            self._local_failures += 1
            if self._local_failures >= self.failure_threshold:
                self._local_open_until = time.monotonic() + self.recovery_timeout
            return

        def _bump() -> int:
            pipe = client.pipeline()
            pipe.incr(self._k_failures)
            pipe.expire(self._k_failures, self.window_seconds)
            return int(pipe.execute()[0])

        try:
            failures = await asyncio.to_thread(_bump)
            if failures >= self.failure_threshold:
                await asyncio.to_thread(
                    client.set, self._k_state, "open", ex=self.recovery_timeout
                )
                # Grace marker outliving the block window; it is what turns the
                # expiry of _k_state into HALF_OPEN rather than plain CLOSED.
                await asyncio.to_thread(
                    client.set, self._k_tripped, "1", ex=self.recovery_timeout * 3
                )
                await asyncio.to_thread(client.delete, self._k_probe)
                logger.error(
                    f"Circuit '{self.name}' OPENED after {failures} failures "
                    f"in {self.window_seconds}s; blocking for {self.recovery_timeout}s"
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Circuit breaker '{self.name}': failure record failed ({exc})")

    # -- public API ---------------------------------------------------------

    async def call(
        self,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Invoke `fn` under breaker protection.

        Raises CircuitOpenError without calling `fn` when the circuit is open.
        Any exception from `fn` counts as a failure and is re-raised unchanged,
        so callers keep their existing error handling.
        """
        allowed, state, retry_after = await self._admit()
        if not allowed:
            raise CircuitOpenError(self.name, retry_after)

        if state is BreakerState.HALF_OPEN:
            logger.info(f"Circuit '{self.name}' HALF_OPEN: admitting probe call")

        try:
            result = await fn(*args, **kwargs)
        except Exception:
            await self._record_failure()
            raise

        if state is BreakerState.HALF_OPEN:
            logger.info(f"Circuit '{self.name}' probe succeeded; CLOSING")
        await self._record_success()
        return result

    async def stats(self) -> BreakerStats:
        client = self._client()
        if client is None:
            now = time.monotonic()
            open_ = now < self._local_open_until
            return BreakerStats(
                name=self.name,
                state=BreakerState.OPEN if open_ else BreakerState.CLOSED,
                failures=self._local_failures,
                retry_after=max(0.0, self._local_open_until - now),
            )
        try:
            raw_state, raw_failures, ttl = await asyncio.to_thread(
                lambda: (
                    client.get(self._k_state),
                    client.get(self._k_failures),
                    client.ttl(self._k_state),
                )
            )
            is_open = raw_state is not None
            return BreakerStats(
                name=self.name,
                state=BreakerState.OPEN if is_open else BreakerState.CLOSED,
                failures=int(raw_failures or 0),
                retry_after=float(ttl or 0) if is_open else 0.0,
            )
        except Exception:  # noqa: BLE001
            return BreakerStats(self.name, BreakerState.CLOSED, 0)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_breakers: Dict[str, CircuitBreaker] = {}


def get_breaker(name: str, **kwargs: Any) -> CircuitBreaker:
    """Fetch (or lazily create) the breaker for a named dependency."""
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name, **kwargs)
    return _breakers[name]


async def all_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Snapshot of every known breaker - surfaced on /health."""
    return {name: (await b.stats()).to_dict() for name, b in _breakers.items()}
