"""
Semantic Deduplication for Synthetic Dataset Generation
=======================================================

Drops near-duplicate generated test cases before they reach the vector index.

WHY THIS IS NOT COSMETIC
------------------------
`dataset_generator.py` samples at temperature 0.7 and validates only structure
(`_validate_test_case`, :482 - field presence and enum membership). Nothing
checked whether row 40 restated row 7. At 1,000 rows per template, LLMs produce
heavy near-duplicates.

Those duplicates then feed a loop that corrupts routing:

    duplicate utterances
      -> indexed as separate rows in the vector store
      -> the same template matches k times for one query
      -> `match_count` for that template inflates
      -> aggregation scores are skewed toward whichever template happened to be
         generated most repetitively

So generation quality silently degrades RETRIEVAL quality. Dedup is a
correctness fix, not tidiness.

BUCKETED, NOT GLOBAL
--------------------
Comparison is scoped to (template_id, scenario_type).

Global dedup would be wrong: two genuinely similar APIs SHOULD have similar
utterances, and collapsing across them starves one template of training rows and
biases routing toward whichever was generated first. Likewise a `valid` case and
an `edge_case` may be phrased alike while testing different behaviour - they
belong to different buckets and must not suppress each other.

THRESHOLD
---------
Default 0.92, configurable, and the observed rate is reported so it can be tuned
against real output.

The originally specified 0.95 is too permissive for short-text embedders:
bge-small places most *unrelated* short English sentences around 0.75-0.85, which
compresses the usable band into the top decile. 0.95 fires rarely enough to miss
obvious restatements. Do not treat 0.92 as sacred - run `calibrate()` on a real
batch and read the histogram.
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from app.core.logger import logger

DEDUP_THRESHOLD = float(os.getenv("DEDUP_THRESHOLD", "0.92"))
DEDUP_ENABLED = os.getenv("DEDUP_ENABLED", "true").lower() in ("1", "true", "yes")


@dataclass
class DedupStats:
    """Reported per generation run so the threshold can be tuned on evidence."""

    total_seen: int = 0
    kept: int = 0
    dropped: int = 0
    threshold: float = DEDUP_THRESHOLD
    per_bucket: Dict[str, Dict[str, int]] = field(default_factory=dict)
    dropped_examples: List[Tuple[str, str, float]] = field(default_factory=list)

    @property
    def dedup_rate(self) -> float:
        return self.dropped / self.total_seen if self.total_seen else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_seen": self.total_seen,
            "kept": self.kept,
            "dropped": self.dropped,
            "dedup_rate": round(self.dedup_rate, 4),
            "threshold": self.threshold,
            "buckets": len(self.per_bucket),
            # A handful of (kept, dropped, similarity) triples make the threshold
            # auditable by eye instead of purely by number.
            "examples": [
                {"kept": k[:90], "dropped": d[:90], "similarity": round(s, 4)}
                for k, d, s in self.dropped_examples[:5]
            ],
        }


class SemanticDeduplicator:
    """
    Greedy incremental dedup.

    Rows are processed in arrival order; each is compared against everything
    already ACCEPTED in its bucket and dropped if it exceeds the threshold
    against any of them. Greedy (rather than clustering the whole batch) because
    generation streams in batches and later rows must be decidable without
    revisiting earlier decisions.

    Cost is O(n * m) dot products per bucket, done as one vectorised matmul per
    candidate. At the 1,000-row target this is milliseconds.
    """

    def __init__(
        self,
        threshold: float = DEDUP_THRESHOLD,
        enabled: bool = DEDUP_ENABLED,
    ) -> None:
        self.threshold = threshold
        self.enabled = enabled
        self._accepted_vecs: Dict[str, List[np.ndarray]] = defaultdict(list)
        self._accepted_texts: Dict[str, List[str]] = defaultdict(list)
        self.stats = DedupStats(threshold=threshold)

    @staticmethod
    def bucket_key(row: Dict[str, Any]) -> str:
        """Comparison scope: same template AND same scenario type."""
        return f"{row.get('template_id', row.get('t_id', 'unknown'))}::{row.get('scenario_type', 'valid')}"

    @staticmethod
    def _normalise(vecs: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vecs, axis=-1, keepdims=True)
        return vecs / np.clip(norms, 1e-9, None)

    def filter_batch(
        self,
        rows: Sequence[Dict[str, Any]],
        embeddings: Sequence[Sequence[float]],
        text_key: str = "query",
    ) -> List[Dict[str, Any]]:
        """
        Return the subset of `rows` that are not near-duplicates.

        `embeddings[i]` must correspond to `rows[i]`. Vectors are L2-normalised
        here, so a dot product is cosine similarity.
        """
        if not rows:
            return []
        if not self.enabled:
            self.stats.total_seen += len(rows)
            self.stats.kept += len(rows)
            return list(rows)

        vecs = self._normalise(np.asarray(embeddings, dtype=np.float32))
        kept: List[Dict[str, Any]] = []

        for row, vec in zip(rows, vecs):
            self.stats.total_seen += 1
            bucket = self.bucket_key(row)
            existing = self._accepted_vecs[bucket]

            if existing:
                sims = np.asarray(existing, dtype=np.float32) @ vec
                worst = int(np.argmax(sims))
                top = float(sims[worst])
                if top >= self.threshold:
                    self.stats.dropped += 1
                    b = self.stats.per_bucket.setdefault(bucket, {"kept": 0, "dropped": 0})
                    b["dropped"] += 1
                    if len(self.stats.dropped_examples) < 25:
                        self.stats.dropped_examples.append(
                            (
                                self._accepted_texts[bucket][worst],
                                str(row.get(text_key, "")),
                                top,
                            )
                        )
                    continue

            self._accepted_vecs[bucket].append(vec)
            self._accepted_texts[bucket].append(str(row.get(text_key, "")))
            b = self.stats.per_bucket.setdefault(bucket, {"kept": 0, "dropped": 0})
            b["kept"] += 1
            self.stats.kept += 1
            kept.append(row)

        return kept

    def report(self) -> Dict[str, Any]:
        s = self.stats
        if s.total_seen:
            logger.info(
                f"Semantic dedup: kept {s.kept}/{s.total_seen} "
                f"({s.dedup_rate:.1%} dropped) across {len(s.per_bucket)} buckets "
                f"@ threshold {s.threshold}"
            )
            if s.dedup_rate > 0.45:
                logger.warning(
                    f"Dedup rate {s.dedup_rate:.1%} is very high - the generator is "
                    f"producing repetitive output. Raise temperature or diversify prompts "
                    f"rather than lowering the threshold."
                )
            elif s.dedup_rate < 0.02 and s.total_seen > 100:
                logger.warning(
                    f"Dedup rate {s.dedup_rate:.1%} is suspiciously low - threshold "
                    f"{s.threshold} may be too permissive for this embedder. Run calibrate()."
                )
        return s.to_dict()


def calibrate(
    texts: Sequence[str],
    embed_fn: Callable[[Sequence[str]], Sequence[Sequence[float]]],
    percentiles: Sequence[int] = (50, 75, 90, 95, 99),
) -> Dict[str, float]:
    """
    Report the pairwise-similarity distribution of a real sample.

    Choose the threshold from this histogram, not from a remembered constant:
    every embedder compresses the similarity range differently. A sensible
    starting point is around the 95th percentile of *within-bucket* pairs.
    """
    vecs = SemanticDeduplicator._normalise(np.asarray(list(embed_fn(texts)), dtype=np.float32))
    sims = vecs @ vecs.T
    iu = np.triu_indices(len(vecs), k=1)
    pairs = sims[iu]
    out = {f"p{p}": float(np.percentile(pairs, p)) for p in percentiles}
    out["mean"] = float(pairs.mean())
    out["max"] = float(pairs.max())
    logger.info(f"Dedup calibration over {len(texts)} texts: {out}")
    return out


_dedup: Optional[SemanticDeduplicator] = None


def get_deduplicator(fresh: bool = False) -> SemanticDeduplicator:
    """
    Fetch the deduplicator.

    `fresh=True` starts a new one - use it per generation run, since accepted-set
    state must not leak between unrelated datasets.
    """
    global _dedup
    if fresh or _dedup is None:
        _dedup = SemanticDeduplicator()
    return _dedup
