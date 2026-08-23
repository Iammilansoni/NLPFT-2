"""
Stage 2 - Cross-Encoder Reranking
==================================

Replaces the v1 `_rerank_by_template` score-aggregation heuristic with a genuine
cross-encoder reranking pass.

WHY THIS EXISTS
---------------
v1 computed:

    final_score = 0.7*avg_similarity + 0.15*avg_confidence + 0.15*intent_alignment

where `avg_similarity` WAS the Stage 1 cosine score. That re-sorts Stage 1's
output by a function of Stage 1's own scores - it is mathematically incapable of
recovering a relevant template that bi-encoder recall ranked poorly, which is the
entire purpose of a reranker.

A cross-encoder jointly encodes (query, passage) through a transformer and emits
a single relevance logit. It sees token-level interaction between the pair, which
a bi-encoder - encoding each side independently - structurally cannot.

PIPELINE POSITION
-----------------
    Stage 1  RECALL     k=50 utterance rows   (bi-encoder / ANN, cheap, high recall)
    Stage 2  PRECISION  k=5  templates        (cross-encoder, costly, high precision)

WHAT GETS CROSS-ENCODED
-----------------------
Utterance ROWS, not template descriptions. Templates carry 500+ word descriptions
(see database_models.py:221) which blow the 512-token window and are off the
distribution ms-marco was trained on. Retrieved rows carry a short natural-language
`query` field - exactly the passage shape the model expects.

ROW -> TEMPLATE AGGREGATION
---------------------------
Aggregation uses MAX by default, not mean.

A template with one perfect utterance match among ten mediocre ones is a BETTER
route than a template with eleven lukewarm ones - but `mean()` (v1 behaviour)
ranks it lower. Max-pooling is the standard passage->document aggregation for
exactly this reason. `mean` is retained only so the eval harness can quantify
the difference.

DEGRADED MODE
-------------
If flashrank is unavailable or the model fails to load, this module does NOT
raise. It returns vector-order results with `degraded=True` so the caller can
surface that honestly rather than silently serving worse routing.
"""

from __future__ import annotations

import asyncio
import math
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.core.logger import logger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# ms-marco-MiniLM-L-12-v2: ~34MB quantised ONNX, the accuracy/latency sweet spot.
# ms-marco-TinyBERT-L-2-v2: ~4MB, ~4x faster, measurably worse - use for
# cold-start-sensitive cloud deploys and justify the swap with eval numbers.
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "ms-marco-MiniLM-L-12-v2")
RERANKER_CACHE_DIR = os.getenv("RERANKER_CACHE_DIR", "/opt/models/flashrank")
RERANKER_ENABLED = os.getenv("RERANKER_ENABLED", "true").lower() in ("1", "true", "yes")

# Stage 1 over-retrieval depth. Recall@k is the ceiling Stage 2 can ever achieve -
# the reranker can only reorder what recall handed it, never add to it.
#
# MEASURED (evals/run_eval.py, 180 held-out queries, tfidf-char3 + MiniLM-L-12):
#     k=15  recall 0.972   Hit@1 0.717
#     k=25  recall 0.978   Hit@1 0.728   p50 265ms   <- chosen
#     k=50  recall 1.000   Hit@1 0.717   p50 482ms
#
# k=50 has strictly better recall yet WORSE Hit@1: handing the cross-encoder more
# marginal candidates gives it more opportunities to be confidently wrong. Recall
# is the ceiling, not the objective. 25 is the measured optimum and costs half
# the latency of 50. Re-run the sweep after any embedder change.
STAGE1_TOP_K = int(os.getenv("STAGE1_TOP_K", "25"))
# Stage 2 output depth.
STAGE2_TOP_K = int(os.getenv("STAGE2_TOP_K", "5"))

AGGREGATION = os.getenv("RERANK_AGGREGATION", "max")  # max | mean | top2mean


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class RerankedTemplate:
    """One template candidate after cross-encoder scoring and aggregation."""

    t_id: str
    ce_score: float                 # aggregated cross-encoder relevance
    vector_score: float             # best Stage 1 cosine, kept for delta analysis
    rank: int = 0
    match_count: int = 0
    api_name: str = ""
    endpoint: str = ""
    method: str = ""
    best_utterance: str = ""        # the row that won the max-pool - explainability
    rows: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "t_id": self.t_id,
            "rank": self.rank,
            "ce_score": round(self.ce_score, 6),
            "vector_score": round(self.vector_score, 6),
            "match_count": self.match_count,
            "api_name": self.api_name,
            "endpoint": self.endpoint,
            "method": self.method,
            "best_utterance": self.best_utterance,
        }


@dataclass
class RerankOutcome:
    """Full Stage 2 output, including honest degradation signalling."""

    templates: List[RerankedTemplate]
    degraded: bool = False
    degraded_reason: Optional[str] = None
    model: str = RERANKER_MODEL
    latency_ms: float = 0.0
    rows_scored: int = 0

    @property
    def best(self) -> Optional[RerankedTemplate]:
        return self.templates[0] if self.templates else None


# ---------------------------------------------------------------------------
# Reranker
# ---------------------------------------------------------------------------

def _sigmoid(x: float) -> float:
    """Numerically stable logistic."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


class CrossEncoderReranker:
    """
    Lazy-loading, thread-offloaded FlashRank wrapper.

    Model load is ~1-2s and inference is CPU-bound, so:
      * load happens once behind an asyncio.Lock (never twice under concurrency)
      * every inference is dispatched via asyncio.to_thread so the event loop
        keeps serving other requests

    Call `warm()` during FastAPI startup to move the load cost off the first
    user request.
    """

    def __init__(
        self,
        model_name: str = RERANKER_MODEL,
        cache_dir: str = RERANKER_CACHE_DIR,
    ) -> None:
        self.model_name = model_name
        self.cache_dir = cache_dir
        self._ranker: Any = None
        self._load_lock = asyncio.Lock()
        self._load_failed_reason: Optional[str] = None

    # -- lifecycle ----------------------------------------------------------

    def _load_sync(self) -> Any:
        """Blocking model load. Never call from the event loop directly."""
        from flashrank import Ranker  # lazily imported: optional dependency

        os.makedirs(self.cache_dir, exist_ok=True)
        t0 = time.perf_counter()
        ranker = Ranker(model_name=self.model_name, cache_dir=self.cache_dir)
        logger.info(
            f"Cross-encoder loaded: {self.model_name} "
            f"({(time.perf_counter() - t0) * 1000:.0f}ms)"
        )
        return ranker

    async def _ensure_loaded(self) -> Optional[Any]:
        if self._ranker is not None:
            return self._ranker
        if self._load_failed_reason is not None:
            return None  # do not retry a hard failure on every request

        async with self._load_lock:
            if self._ranker is not None:          # another coroutine won the race
                return self._ranker
            if self._load_failed_reason is not None:
                return None
            try:
                self._ranker = await asyncio.to_thread(self._load_sync)
                return self._ranker
            except ImportError as exc:
                self._load_failed_reason = f"flashrank not installed ({exc})"
            except Exception as exc:  # noqa: BLE001 - degrade, never crash routing
                self._load_failed_reason = f"model load failed ({exc})"
            logger.error(f"Cross-encoder unavailable: {self._load_failed_reason}")
            return None

    async def warm(self) -> bool:
        """Preload at startup. Returns True if the model is ready."""
        if not RERANKER_ENABLED:
            logger.warning("Cross-encoder disabled via RERANKER_ENABLED=false")
            return False
        return await self._ensure_loaded() is not None

    @property
    def is_ready(self) -> bool:
        return self._ranker is not None

    # -- inference ----------------------------------------------------------

    def _rerank_sync(self, query: str, passages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        from flashrank import RerankRequest

        return self._ranker.rerank(RerankRequest(query=query, passages=passages))

    async def rerank_rows(
        self,
        query: str,
        rows: Sequence[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Cross-encode (query, row["query"]) for every Stage 1 row.

        Returns (rows_with_ce_score, degraded_reason). On degradation the rows come
        back in vector order with `ce_score` mirroring `similarity`, so downstream
        aggregation stays uniform either way.
        """
        if not rows:
            return [], None

        if not RERANKER_ENABLED:
            return self._fallback(rows), "reranker disabled"

        ranker = await self._ensure_loaded()
        if ranker is None:
            return self._fallback(rows), self._load_failed_reason

        # FlashRank addresses passages by id; use the index into the original list.
        passages = [
            {"id": idx, "text": (row.get("query") or "").strip(), "meta": {}}
            for idx, row in enumerate(rows)
        ]
        passages = [p for p in passages if p["text"]]
        if not passages:
            return self._fallback(rows), "no utterance text on retrieved rows"

        try:
            scored = await asyncio.to_thread(self._rerank_sync, query, passages)
        except Exception as exc:  # noqa: BLE001 - degrade, never crash routing
            logger.error(f"Cross-encoder inference failed: {exc}")
            return self._fallback(rows), f"inference failed ({exc})"

        # FlashRank emits raw logits or probabilities depending on the model.
        # Normalise to [0,1] so scores are comparable across models and the eval
        # harness can chart them on one axis.
        raw = [float(s.get("score", 0.0)) for s in scored]
        needs_sigmoid = any(v < 0.0 or v > 1.0 for v in raw)

        out = [dict(row) for row in rows]
        for row in out:
            row["ce_score"] = 0.0
            row["ce_scored"] = False

        for item in scored:
            idx = int(item["id"])
            val = float(item.get("score", 0.0))
            out[idx]["ce_score"] = _sigmoid(val) if needs_sigmoid else val
            out[idx]["ce_scored"] = True

        out.sort(key=lambda r: r["ce_score"], reverse=True)
        return out, None

    @staticmethod
    def _fallback(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Vector-order passthrough. ce_score mirrors cosine so callers stay uniform."""
        out = [dict(r) for r in rows]
        for r in out:
            r["ce_score"] = float(r.get("similarity", 0.0))
            r["ce_scored"] = False
        out.sort(key=lambda r: r["ce_score"], reverse=True)
        return out

    # -- aggregation --------------------------------------------------------

    @staticmethod
    def aggregate_to_templates(
        scored_rows: Sequence[Dict[str, Any]],
        strategy: str = AGGREGATION,
        top_k: int = STAGE2_TOP_K,
    ) -> List[RerankedTemplate]:
        """
        Collapse cross-encoded rows into ranked template candidates.

        max (default): a template is as good as its single best-matching utterance.
        mean:          v1 behaviour, retained for eval comparison only.
        top2mean:      compromise; rewards two corroborating strong matches.
        """
        buckets: Dict[str, List[Dict[str, Any]]] = {}
        for row in scored_rows:
            t_id = row.get("t_id") or row.get("template_id")
            if not t_id:
                continue
            buckets.setdefault(str(t_id), []).append(row)

        candidates: List[RerankedTemplate] = []
        for t_id, rows in buckets.items():
            rows.sort(key=lambda r: r.get("ce_score", 0.0), reverse=True)
            ce = [float(r.get("ce_score", 0.0)) for r in rows]

            if strategy == "mean":
                agg = sum(ce) / len(ce)
            elif strategy == "top2mean":
                agg = sum(ce[:2]) / min(2, len(ce))
            else:  # max
                agg = ce[0]

            best_row = rows[0]
            candidates.append(
                RerankedTemplate(
                    t_id=t_id,
                    ce_score=agg,
                    vector_score=max(float(r.get("similarity", 0.0)) for r in rows),
                    match_count=len(rows),
                    api_name=best_row.get("api_name", ""),
                    endpoint=best_row.get("endpoint", ""),
                    method=best_row.get("method", ""),
                    best_utterance=(best_row.get("query") or "")[:200],
                    rows=rows,
                )
            )

        candidates.sort(key=lambda c: c.ce_score, reverse=True)
        for i, c in enumerate(candidates):
            c.rank = i + 1
        return candidates[:top_k]

    # -- public entrypoint --------------------------------------------------

    async def run(
        self,
        query: str,
        stage1_rows: Sequence[Dict[str, Any]],
        top_k: int = STAGE2_TOP_K,
        strategy: str = AGGREGATION,
    ) -> RerankOutcome:
        """Full Stage 2: cross-encode rows -> aggregate -> top-k templates."""
        t0 = time.perf_counter()
        scored, degraded_reason = await self.rerank_rows(query, stage1_rows)
        templates = self.aggregate_to_templates(scored, strategy=strategy, top_k=top_k)
        return RerankOutcome(
            templates=templates,
            degraded=degraded_reason is not None,
            degraded_reason=degraded_reason,
            model=self.model_name,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            rows_scored=sum(1 for r in scored if r.get("ce_scored")),
        )


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_reranker: Optional[CrossEncoderReranker] = None


def get_reranker() -> CrossEncoderReranker:
    """Process-wide singleton. The model is loaded at most once per process."""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker()
    return _reranker
