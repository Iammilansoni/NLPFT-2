"""
Extraction benchmark runner.

Scores how well request-body values are extracted from the 100 cases in
extraction_cases.py, per strategy:

    llm     the LLM alone (the v2 behaviour: schema-constrained decoding)
    rules   deterministic rules only, no model call
    hybrid  rules first, the LLM only for what rules did not find, then a
            grounding check on the LLM's values (the shipped default)

Metrics
    precision      extracted values that are correct
    recall         expected values that were extracted
    exact          requests whose whole body is exactly right
    invented       values extracted for fields the request never mentioned
    p50 / p95 ms   extraction latency
    llm calls      share of requests that needed the model at all

Runs inside the backend container (it needs the app and Ollama):
    docker cp evals nlpft-2-backend-1:/tmp/evals
    docker exec -w /app nlpft-2-backend-1 python /tmp/evals/run_extraction_eval.py --strategy hybrid
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
for candidate in (HERE.parent / "Backend", Path("/app")):
    if (candidate / "app").exists():
        sys.path.insert(0, str(candidate))
        break

from extraction_cases import ANY_ITEMS, CASES  # noqa: E402

from app.demo_catalogue import API_TEMPLATES  # noqa: E402

SCHEMAS = {t["api_name"]: t["json_schema"] for t in API_TEMPLATES}
ENDPOINTS = {t["api_name"]: t["endpoint"] for t in API_TEMPLATES}

# Free text is compared loosely (case, punctuation, a trailing "s"); identifiers,
# secrets and codes must match character for character.
FREE_TEXT = {"reason", "body", "full_name", "timezone", "role"}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9/_ ]+", "", str(text).lower()).strip()


def matches(field: str, expected: Any, got: Any) -> bool:
    if expected == ANY_ITEMS:
        return isinstance(got, list) and len(got) > 0
    if isinstance(expected, bool):
        return got is expected
    if isinstance(expected, (int, float)):
        try:
            return abs(float(got) - float(expected)) < 1e-6
        except (TypeError, ValueError):
            return False
    if "email" in field:
        return str(got).strip().lower() == str(expected).lower()
    if field in FREE_TEXT:
        a, b = _norm(expected), _norm(got)
        if not a or not b:
            return False
        shorter, longer = sorted((a, b), key=len)
        return shorter in longer and len(shorter) / len(longer) >= 0.6
    return str(got).strip() == str(expected)


def score(cases: List[Dict[str, Any]], outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    correct = wrong = invented = missed = exact = 0
    for case, got in zip(cases, outputs):
        expected = case["expected"]
        case_ok = True
        for field, value in expected.items():
            if field not in got:
                missed += 1
                case_ok = False
            elif matches(field, value, got[field]):
                correct += 1
            else:
                wrong += 1
                case_ok = False
        extra = [f for f in got if f not in expected]
        invented += len(extra)
        if extra:
            case_ok = False
        exact += case_ok
    extracted = correct + wrong + invented
    gold = sum(len(c["expected"]) for c in cases)
    return {
        "precision": correct / extracted if extracted else 1.0,
        "recall": correct / gold if gold else 1.0,
        "exact": exact / len(cases),
        "invented": invented,
        "wrong": wrong,
        "missed": missed,
    }


async def run(strategy: str) -> Tuple[List[Dict[str, Any]], List[float], int]:
    from app.services.structured_extraction_service import get_structured_extraction_service

    service = get_structured_extraction_service()
    await service.warm()
    outputs, latencies, llm_calls = [], [], 0
    for i, case in enumerate(CASES):
        t0 = time.perf_counter()
        result = await service.extract(
            query=case["query"],
            request_schema=SCHEMAS[case["api"]],
            api_name=case["api"],
            endpoint=ENDPOINTS[case["api"]],
            strategy=strategy,
        )
        latencies.append((time.perf_counter() - t0) * 1000)
        llm_calls += bool(result.attempts)
        outputs.append(result.values)
        if result.degraded:
            print(f"  degraded on case {i}: {result.reason}", flush=True)
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(CASES)}", flush=True)
    return outputs, latencies, llm_calls


def main() -> int:
    parser = argparse.ArgumentParser(description="NLPForge extraction benchmark")
    parser.add_argument("--strategy", choices=["llm", "rules", "hybrid"], default="hybrid")
    parser.add_argument("--show-errors", action="store_true")
    parser.add_argument("--out", help="write per-case results as JSON here")
    args = parser.parse_args()

    outputs, latencies, llm_calls = asyncio.run(run(args.strategy))
    metrics = score(CASES, outputs)
    lat = sorted(latencies)
    print(
        f"\n{args.strategy:<7} precision {metrics['precision']:.3f}  recall {metrics['recall']:.3f}  "
        f"exact {metrics['exact']:.3f}  invented {metrics['invented']}  wrong {metrics['wrong']}  "
        f"missed {metrics['missed']}  p50 {statistics.median(lat):.0f}ms  "
        f"p95 {lat[int(len(lat) * 0.95) - 1]:.0f}ms  llm calls {llm_calls}/{len(CASES)}"
    )
    if args.show_errors:
        for case, got in zip(CASES, outputs):
            bad = [f for f, v in case["expected"].items() if f not in got or not matches(f, v, got[f])]
            extra = [f for f in got if f not in case["expected"]]
            if bad or extra:
                print(f"  {case['query']!r}\n    expected {case['expected']}\n    got      {got}")
    if args.out:
        Path(args.out).write_text(json.dumps(
            [{"case": c, "got": g} for c, g in zip(CASES, outputs)], indent=1, default=str
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
