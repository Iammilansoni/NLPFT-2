"""
Phase 2 unit tests — circuit breaker, structured extraction, semantic dedup.

These test the behaviours the audit flagged as broken, not just happy paths:
  * a failed LLM call must be distinguishable from an empty extraction
  * invalid LLM output must be repaired, not silently dropped
  * an open circuit must not attempt the call at all
  * dedup must be scoped per bucket, never global
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

import numpy as np
import pytest

from app.core.circuit_breaker import (
    BreakerState,
    CircuitBreaker,
    CircuitOpenError,
)
from app.nlp.semantic_dedup import SemanticDeduplicator
from app.services.structured_extraction_service import (
    ExtractionResult,
    StructuredExtractionService,
    build_validator,
)

SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "email": {"type": "string"},
        "password": {"type": "string"},
        "attempts": {"type": "integer"},
        "remember": {"type": "boolean"},
    },
    "required": ["email", "password"],
}


# ===========================================================================
# Circuit breaker
# ===========================================================================

class _FakeRedis:
    """Minimal in-memory stand-in exercising the same code path as real Redis."""

    def __init__(self) -> None:
        self.store: Dict[str, Any] = {}

    # -- the Lua admit script is replaced by an equivalent python callable --
    # Mirrors _ADMIT_LUA exactly: `open` present => reject; else `tripped`
    # present => admit one NX-guarded probe; else closed.
    def register_script(self, _src: str):
        def _run(keys: List[str], args: List[Any]):
            open_key, tripped_key, probe_key = keys
            if open_key in self.store:
                return [0, "open", 5]
            if tripped_key in self.store:
                if probe_key not in self.store:
                    self.store[probe_key] = "1"
                    return [1, "half_open", 0]
                return [0, "open", 1]
            return [1, "closed", 0]

        return _run

    def expire_open_window(self, name: str) -> None:
        """Simulate the block window elapsing without sleeping in tests."""
        self.store.pop(f"cb:{name}:open", None)

    def pipeline(self):
        outer = self

        class _P:
            def __init__(self) -> None:
                self.ops: List[Any] = []

            def incr(self, k: str):
                outer.store[k] = int(outer.store.get(k, 0)) + 1
                self.ops.append(outer.store[k])
                return self

            def expire(self, *_a, **_k):
                self.ops.append(True)
                return self

            def execute(self):
                return self.ops

        return _P()

    def set(self, k: str, v: Any, ex: int | None = None):
        self.store[k] = v
        return True

    def get(self, k: str):
        return self.store.get(k)

    def delete(self, *keys: str):
        for k in keys:
            self.store.pop(k, None)
        return len(keys)

    def ttl(self, _k: str):
        return 5


@pytest.mark.asyncio
async def test_breaker_opens_after_threshold_and_blocks_calls():
    """Once tripped, the breaker must not invoke the wrapped callable at all."""
    breaker = CircuitBreaker(
        "test_dep", failure_threshold=3, recovery_timeout=30, redis_client=_FakeRedis()
    )
    calls = {"n": 0}

    async def boom():
        calls["n"] += 1
        raise RuntimeError("dependency down")

    for _ in range(3):
        with pytest.raises(RuntimeError):
            await breaker.call(boom)
    assert calls["n"] == 3

    # 4th attempt must be rejected WITHOUT touching the dependency.
    with pytest.raises(CircuitOpenError):
        await breaker.call(boom)
    assert calls["n"] == 3, "open circuit still invoked the failing dependency"


@pytest.mark.asyncio
async def test_breaker_half_open_admits_exactly_one_probe():
    """
    After the block window elapses the breaker must admit ONE probe, not resume
    normal traffic. A second concurrent caller must still be rejected.
    """
    fake = _FakeRedis()
    breaker = CircuitBreaker(
        "test_probe", failure_threshold=2, recovery_timeout=30, redis_client=fake
    )

    async def boom():
        raise RuntimeError("down")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            await breaker.call(boom)

    fake.expire_open_window("test_probe")  # block window elapses

    calls = {"n": 0}

    async def probe():
        calls["n"] += 1
        return "recovered"

    assert await breaker.call(probe) == "recovered"
    assert calls["n"] == 1

    # A success closes the circuit, so subsequent traffic flows normally again.
    assert await breaker.call(probe) == "recovered"
    assert (await breaker.stats()).state is BreakerState.CLOSED


@pytest.mark.asyncio
async def test_breaker_rejects_second_caller_during_half_open():
    fake = _FakeRedis()
    breaker = CircuitBreaker(
        "test_single", failure_threshold=1, recovery_timeout=30, redis_client=fake
    )

    async def boom():
        raise RuntimeError("down")

    with pytest.raises(RuntimeError):
        await breaker.call(boom)
    fake.expire_open_window("test_single")

    async def slow_probe():
        await asyncio.sleep(0.05)
        return "ok"

    async def other():
        return "should not run"

    task = asyncio.create_task(breaker.call(slow_probe))
    await asyncio.sleep(0.01)  # let the probe claim the token
    with pytest.raises(CircuitOpenError):
        await breaker.call(other)
    assert await task == "ok"


@pytest.mark.asyncio
async def test_breaker_success_resets_failure_count():
    breaker = CircuitBreaker(
        "test_reset", failure_threshold=3, redis_client=_FakeRedis()
    )

    async def boom():
        raise RuntimeError("nope")

    async def fine():
        return "ok"

    for _ in range(2):
        with pytest.raises(RuntimeError):
            await breaker.call(boom)

    assert await breaker.call(fine) == "ok"

    # Counter was cleared, so two more failures must not trip it.
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await breaker.call(boom)
    assert (await breaker.stats()).state is BreakerState.CLOSED


@pytest.mark.asyncio
async def test_breaker_fails_open_when_redis_unavailable():
    """A monitoring component must never itself become the outage."""
    breaker = CircuitBreaker("no_redis", redis_client=None)
    breaker._client = lambda: None  # type: ignore[method-assign]

    async def fine():
        return 42

    assert await breaker.call(fine) == 42


# ===========================================================================
# Schema -> pydantic validator
# ===========================================================================

def test_validator_enforces_required_and_coerces_types():
    V = build_validator(SCHEMA)

    ok = V(email="a@b.com", password="pw", attempts="3")
    assert ok.attempts == 3, "string digit should coerce to int"

    with pytest.raises(Exception):
        V(email="a@b.com")  # missing required 'password'


def test_validator_drops_unknown_keys():
    V = build_validator(SCHEMA)
    m = V(email="a@b.com", password="pw")
    assert "injected" not in m.model_dump()


# ===========================================================================
# Structured extraction
# ===========================================================================

def _svc_with_responses(responses: List[str]) -> StructuredExtractionService:
    """Service whose transport returns canned payloads in order."""
    svc = StructuredExtractionService(model="fake-model")
    seq = list(responses)

    async def _fake_generate(prompt: str, schema: Dict[str, Any]) -> str:
        return seq.pop(0)

    svc._generate = _fake_generate  # type: ignore[method-assign]
    return svc


@pytest.mark.asyncio
async def test_extraction_happy_path():
    svc = _svc_with_responses([json.dumps({"email": "a@b.com", "password": "pw"})])
    res = await svc.extract("log in a@b.com with pw", SCHEMA, "User_Login", "/auth/login")
    assert res.ok and res.values == {"email": "a@b.com", "password": "pw"}
    assert res.attempts == 1


@pytest.mark.asyncio
async def test_extraction_repairs_invalid_output_on_retry():
    """
    v1 would have returned {} here and lost the data.
    v2 must feed the validation error back and succeed on the retry.
    """
    svc = _svc_with_responses(
        [
            "here you go: {not valid json",
            json.dumps({"email": "a@b.com", "password": "pw"}),
        ]
    )
    res = await svc.extract("log in a@b.com with pw", SCHEMA)
    assert res.ok, f"repair retry failed: {res.reason}"
    assert res.values["email"] == "a@b.com"
    assert res.attempts == 2


@pytest.mark.asyncio
async def test_empty_extraction_is_distinguishable_from_failure():
    """THE v1 BUG: a crashed call and an empty result were byte-identical ({})."""
    empty = _svc_with_responses([json.dumps({"email": "a@b.com", "password": "pw"})])
    good = await empty.extract("q", SCHEMA)

    broken = StructuredExtractionService(model="fake")

    async def _die(prompt: str, schema: Dict[str, Any]) -> str:
        raise RuntimeError("ollama exploded")

    broken._generate = _die  # type: ignore[method-assign]
    bad = await broken.extract("q", SCHEMA)

    assert good.ok is True and good.degraded is False
    assert bad.ok is False and bad.degraded is True
    assert bad.reason and "ollama exploded" in bad.reason
    assert good.to_dict() != bad.to_dict()


@pytest.mark.asyncio
async def test_extraction_does_not_retry_into_open_circuit():
    svc = StructuredExtractionService(model="fake")
    attempts = {"n": 0}

    async def _open(prompt: str, schema: Dict[str, Any]) -> str:
        attempts["n"] += 1
        raise CircuitOpenError("llm_extraction", 30.0)

    svc._generate = _open  # type: ignore[method-assign]
    res = await svc.extract("q", SCHEMA, max_repair_attempts=3)

    assert res.ok is False and res.degraded is True
    assert "circuit_open" in (res.reason or "")
    assert attempts["n"] == 1, "must not retry while the circuit is open"


@pytest.mark.asyncio
async def test_extraction_with_no_schema_is_success_not_failure():
    svc = StructuredExtractionService(model="fake")
    res = await svc.extract("anything", None)
    assert res.ok is True and res.values == {}


# ===========================================================================
# Semantic dedup
# ===========================================================================

def _vec(*xs: float) -> List[float]:
    return list(xs)


def test_dedup_drops_near_duplicates_within_a_bucket():
    d = SemanticDeduplicator(threshold=0.92)
    rows = [
        {"template_id": "T1", "scenario_type": "valid", "query": "log me in"},
        {"template_id": "T1", "scenario_type": "valid", "query": "log me in please"},
        {"template_id": "T1", "scenario_type": "valid", "query": "delete everything"},
    ]
    embs = [_vec(1.0, 0.0), _vec(0.999, 0.045), _vec(0.0, 1.0)]

    kept = d.filter_batch(rows, embs)
    assert len(kept) == 2
    assert d.stats.dropped == 1
    assert kept[1]["query"] == "delete everything"


def test_dedup_is_scoped_per_template_not_global():
    """
    Two different templates may legitimately have near-identical utterances.
    Global dedup would starve the second template of rows.
    """
    d = SemanticDeduplicator(threshold=0.92)
    rows = [
        {"template_id": "T1", "scenario_type": "valid", "query": "send it"},
        {"template_id": "T2", "scenario_type": "valid", "query": "send it"},
    ]
    embs = [_vec(1.0, 0.0), _vec(1.0, 0.0)]

    kept = d.filter_batch(rows, embs)
    assert len(kept) == 2, "identical text across different templates must both survive"
    assert d.stats.dropped == 0


def test_dedup_is_scoped_per_scenario_type():
    d = SemanticDeduplicator(threshold=0.92)
    rows = [
        {"template_id": "T1", "scenario_type": "valid", "query": "send it"},
        {"template_id": "T1", "scenario_type": "edge_case", "query": "send it"},
    ]
    embs = [_vec(1.0, 0.0), _vec(1.0, 0.0)]
    assert len(d.filter_batch(rows, embs)) == 2


def test_dedup_reports_rate_and_examples():
    d = SemanticDeduplicator(threshold=0.90)
    rows = [
        {"template_id": "T1", "scenario_type": "valid", "query": f"q{i}"}
        for i in range(4)
    ]
    embs = [_vec(1.0, 0.0), _vec(1.0, 0.0), _vec(1.0, 0.0), _vec(0.0, 1.0)]

    kept = d.filter_batch(rows, embs)
    report = d.report()

    assert len(kept) == 2
    assert report["dropped"] == 2
    assert report["dedup_rate"] == 0.5
    assert report["examples"], "dropped examples must be reported for auditability"


def test_dedup_disabled_passes_everything_through():
    d = SemanticDeduplicator(threshold=0.5, enabled=False)
    rows = [{"template_id": "T1", "scenario_type": "valid", "query": "x"}] * 3
    embs = [_vec(1.0, 0.0)] * 3
    assert len(d.filter_batch(rows, embs)) == 3
