"""
Reciprocal Rank Fusion
======================

Combines several ranked lists into one without needing their scores to be
comparable.

WHY RRF AND NOT SCORE BLENDING
------------------------------
The obvious alternative - `alpha * cosine + (1-alpha) * bm25` - requires the two
score distributions to live on a common scale. They do not. Cosine is bounded in
[-1, 1] and, for a short-text embedder, is empirically compressed into roughly
[0.75, 0.95]. BM25 is unbounded above and its range shifts with corpus size,
document length, and how rare the query terms happen to be. Any fixed `alpha`
is therefore tuned to one corpus and silently wrong on the next.

That is not a hypothetical concern here. NLPForge v1 already shipped one
hand-weighted score blend:

    0.7*avg_similarity + 0.15*avg_confidence + 0.15*intent_alignment

and the benchmark measured it at 0.444 Hit@1 against a 0.617 vector-only
baseline - a 17-point REGRESSION caused precisely by mixing incommensurable
quantities under invented weights. Repeating that mistake with cosine and BM25
would be an unforced error.

RRF discards magnitudes and keeps only RANK:

    RRF(d) = SUM_r  1 / (k + rank_r(d))

A document ranked 1st by either retriever contributes 1/(k+1) regardless of
whether its cosine was 0.94 or its BM25 was 31.7. There is nothing to calibrate
and nothing to re-tune per corpus.

CHOOSING k
----------
k=60 is the value from Cormack et al. (2009), where RRF was introduced, and is
the near-universal default. It damps the influence of top ranks just enough that
a single retriever cannot dominate the fusion on its own. Larger k flattens
toward a rank-agnostic vote; smaller k lets rank 1 dominate.

WEIGHTING
---------
`weights` scales each retriever's contribution. Default is equal weighting.
Prefer leaving it equal: a weight is a tuned constant, and tuning it on the same
queries used to report results is fitting the benchmark. It exists for the case
where one retriever is known a priori to be far weaker.
"""

from __future__ import annotations

from typing import Dict, Hashable, List, Optional, Sequence, Tuple, TypeVar

T = TypeVar("T", bound=Hashable)

RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[T]],
    k: int = RRF_K,
    weights: Optional[Sequence[float]] = None,
    top_k: Optional[int] = None,
) -> List[Tuple[T, float]]:
    """
    Fuse ranked lists into one.

    Args:
        ranked_lists: each an iterable of ids in descending relevance. Lists may
            be different lengths and need not cover the same ids.
        k: RRF damping constant.
        weights: per-list multipliers; defaults to equal weighting.
        top_k: truncate the fused output.

    Returns:
        [(id, fused_score)] descending. Ties break on first appearance, which
        keeps the output deterministic across runs.
    """
    if not ranked_lists:
        return []

    w = list(weights) if weights is not None else [1.0] * len(ranked_lists)
    if len(w) != len(ranked_lists):
        raise ValueError(
            f"weights has {len(w)} entries for {len(ranked_lists)} ranked lists"
        )

    scores: Dict[T, float] = {}
    first_seen: Dict[T, int] = {}
    order = 0

    for weight, ranked in zip(w, ranked_lists):
        for rank, item in enumerate(ranked, start=1):
            scores[item] = scores.get(item, 0.0) + weight / (k + rank)
            if item not in first_seen:
                first_seen[item] = order
                order += 1

    fused = sorted(scores.items(), key=lambda kv: (-kv[1], first_seen[kv[0]]))
    return fused[:top_k] if top_k else fused


def fuse_result_rows(
    vector_rows: Sequence[dict],
    lexical_rows: Sequence[dict],
    id_key: str = "redis_key",
    k: int = RRF_K,
    top_k: Optional[int] = None,
    weights: Optional[Sequence[float]] = None,
) -> List[dict]:
    """
    Convenience wrapper for the pipeline's row dicts.

    Returns row dicts carrying `rrf_score` and `fusion_sources` (which retrievers
    surfaced the row), preserving whatever other fields the rows already had.
    `fusion_sources` matters for debugging: a row found by both arms is a far
    stronger signal than one found by either alone.
    """
    by_id: Dict[Hashable, dict] = {}
    sources: Dict[Hashable, List[str]] = {}

    for tag, rows in (("vector", vector_rows), ("lexical", lexical_rows)):
        for row in rows:
            rid = row.get(id_key)
            if rid is None:
                continue
            by_id.setdefault(rid, dict(row))
            sources.setdefault(rid, []).append(tag)

    fused = reciprocal_rank_fusion(
        [
            [r[id_key] for r in vector_rows if r.get(id_key) is not None],
            [r[id_key] for r in lexical_rows if r.get(id_key) is not None],
        ],
        k=k,
        weights=weights,
        top_k=top_k,
    )

    out: List[dict] = []
    for rid, score in fused:
        row = by_id[rid]
        row["rrf_score"] = score
        row["fusion_sources"] = sources.get(rid, [])
        out.append(row)
    return out
