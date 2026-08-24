#!/usr/bin/env python
"""
NLPForge Routing Benchmark
==========================

Measures how well the two-stage pipeline routes natural language to the correct
API template, and quantifies exactly what Stage 2 contributes.

WHY THIS IS SELF-CONTAINED
--------------------------
The harness builds its own in-memory index from `api_surface.py` utterances. It
needs no PostgreSQL, no Redis, no running API — so it runs in CI on every push
and can gate a merge on routing accuracy.

It also uses BRUTE-FORCE exact cosine for Stage 1 rather than ANN. That is
deliberate: ANN recall loss and reranker quality are different failure modes, and
mixing them makes the numbers uninterpretable. Exact recall isolates the
reranker's contribution. HNSW recall-vs-latency is a separate experiment
(`--report-ann`, tracked separately).

THE THREE STRATEGIES COMPARED
-----------------------------
stage1_only        Vector similarity, max-pooled to template. The honest baseline.

v1_heuristic       The shipped-in-v1 formula, reproduced faithfully:
                     0.7*avg_sim + 0.15*avg_conf + 0.15*intent_align,
                     mean-aggregated, with the >=0.85 similarity 1.1x boost.
                   Included to demonstrate empirically that it was not a reranker.

v2_cross_encoder   FlashRank ms-marco cross-encoder, max-pooled to template.

Reporting all three is the point. "We added a reranker" is a claim; "Hit@1 on
hard negatives went 0.42 -> 0.78 while v1's heuristic scored 0.44" is evidence.

USAGE
-----
    python evals/run_eval.py                        # tfidf embedder, zero deps
    python evals/run_eval.py --embedder onnx        # bge-small-en-v1.5
    python evals/run_eval.py --embedder ollama --model nomic-embed-text
    python evals/run_eval.py --markdown results.md  # emit README table
    python evals/run_eval.py --fail-under 0.75      # CI gate on Hit@1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# Make `app.*` importable when run from the repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "Backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# The harness MEASURES the reranker, so it forces it on regardless of the
# shipped default (which is now off - see cross_encoder_reranker.py). This must
# happen before the app import, since the module reads the flag at import time.
os.environ.setdefault("RERANKER_ENABLED", "true")

from api_surface import API_TEMPLATES, TEMPLATES_BY_NAME, cluster_of  # noqa: E402
from benchmark_queries import TIERS, load_benchmark  # noqa: E402

# Default to whatever PRODUCTION defaults to, so the benchmark measures the
# pipeline that actually ships. Hard-coding a separate default here silently
# decoupled the two: the app moved to k=25 while CI kept reporting k=50.
# Override with EVAL_STAGE1_K only to run a sweep.
from app.nlp.cross_encoder_reranker import (  # noqa: E402
    STAGE1_TOP_K as _PROD_STAGE1_K,
    STAGE2_TOP_K as _PROD_STAGE2_K,
)
from app.nlp.fusion import fuse_result_rows  # noqa: E402
from app.nlp.lexical_bm25 import BM25Index  # noqa: E402

STAGE1_K = int(os.getenv("EVAL_STAGE1_K", str(_PROD_STAGE1_K)))
STAGE2_K = int(os.getenv("EVAL_STAGE2_K", str(_PROD_STAGE2_K)))


# ===========================================================================
# Embedders
# ===========================================================================

class Embedder:
    name = "base"
    dim = 0

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        raise NotImplementedError


class TfidfEmbedder(Embedder):
    """
    Dependency-free character n-gram TF-IDF.

    This is a genuine lexical baseline, not a stub. It gives the harness a mode
    that always runs (CI, no model downloads) and doubles as the lexical arm of
    the hybrid-retrieval experiment: if the cross-encoder lifts Hit@1 on top of
    TF-IDF recall, that lift is real and not an artefact of a strong embedder.
    """

    name = "tfidf-char3"

    def __init__(self, ngram: int = 3):
        self.ngram = ngram
        self.vocab: Dict[str, int] = {}
        self.idf: Optional[np.ndarray] = None

    @staticmethod
    def _norm(text: str) -> str:
        return " " + "".join(c.lower() if c.isalnum() else " " for c in text).strip() + " "

    def _grams(self, text: str) -> List[str]:
        t = self._norm(text)
        n = self.ngram
        return [t[i : i + n] for i in range(max(0, len(t) - n + 1))]

    def fit(self, corpus: Sequence[str]) -> None:
        df: Dict[str, int] = defaultdict(int)
        for doc in corpus:
            for g in set(self._grams(doc)):
                df[g] += 1
        self.vocab = {g: i for i, g in enumerate(sorted(df))}
        n_docs = len(corpus)
        self.idf = np.zeros(len(self.vocab), dtype=np.float32)
        for g, i in self.vocab.items():
            self.idf[i] = math.log((1 + n_docs) / (1 + df[g])) + 1.0
        self.dim = len(self.vocab)

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        assert self.idf is not None, "call fit() before encode()"
        out = np.zeros((len(texts), len(self.vocab)), dtype=np.float32)
        for r, text in enumerate(texts):
            for g in self._grams(text):
                idx = self.vocab.get(g)
                if idx is not None:
                    out[r, idx] += 1.0
        out *= self.idf
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.clip(norms, 1e-9, None)


class OnnxEmbedder(Embedder):
    """bge-small-en-v1.5 via fastembed — the Cloud-mode in-process embedder."""

    name = "bge-small-en-v1.5"
    dim = 384

    def __init__(self) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        vecs = np.array(list(self._model.embed(list(texts))), dtype=np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.clip(norms, 1e-9, None)


class OllamaEmbedder(Embedder):
    """Local-mode embedder, reusing the app's own Ollama service."""

    def __init__(self, model: str = "nomic-embed-text") -> None:
        from app.services.ollama_embedding_service import get_ollama_service

        self.name = f"ollama:{model}"
        self.model = model
        self._svc = get_ollama_service()

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        async def _run() -> List[List[float]]:
            return await self._svc.generate_embeddings_batch(self.model, list(texts))

        vecs = np.array(asyncio.run(_run()), dtype=np.float32)
        self.dim = vecs.shape[1]
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.clip(norms, 1e-9, None)


def build_embedder(kind: str, model: str) -> Embedder:
    if kind == "onnx":
        return OnnxEmbedder()
    if kind == "ollama":
        return OllamaEmbedder(model)
    return TfidfEmbedder()


# ===========================================================================
# Index
# ===========================================================================

class UtteranceIndex:
    """
    Flat exact-cosine index over every template utterance, plus a parallel BM25
    index over the same rows so hybrid fusion can be measured against the
    identical corpus.
    """

    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.rows: List[Dict[str, Any]] = []
        self.matrix: Optional[np.ndarray] = None
        self.bm25: Optional[BM25Index] = None

    def build(self) -> None:
        for tpl in API_TEMPLATES:
            for utt in tpl["utterances"]:
                self.rows.append(
                    {
                        "query": utt,
                        "t_id": tpl["api_name"],   # api_name doubles as stable t_id
                        "api_name": tpl["api_name"],
                        "endpoint": tpl["endpoint"],
                        "method": tpl["method"],
                        "intent_type": "action" if tpl["method"] != "GET" else "info",
                        "confidence_score": 0.7,   # v1 default (see audit gap 1)
                    }
                )
        # Every row carries a stable id so the two retrievers' outputs can be
        # fused by identity rather than by position.
        for i, row in enumerate(self.rows):
            row["row_key"] = f"r{i}"

        corpus = [r["query"] for r in self.rows]
        if isinstance(self.embedder, TfidfEmbedder):
            self.embedder.fit(corpus)
        self.matrix = self.embedder.encode(corpus)
        self.bm25 = BM25Index().build(corpus)

    def search(self, query: str, top_k: int = STAGE1_K) -> Tuple[List[Dict[str, Any]], float]:
        assert self.matrix is not None
        t0 = time.perf_counter()
        qv = self.embedder.encode([query])[0]
        sims = self.matrix @ qv
        k = min(top_k, len(sims))
        idx = np.argpartition(-sims, k - 1)[:k]
        idx = idx[np.argsort(-sims[idx])]
        out = []
        for i in idx:
            row = dict(self.rows[int(i)])
            row["similarity"] = float(sims[int(i)])
            out.append(row)
        return out, (time.perf_counter() - t0) * 1000.0

    def search_lexical(
        self, query: str, top_k: int = STAGE1_K
    ) -> Tuple[List[Dict[str, Any]], float]:
        """BM25 arm. Returns the same row shape as `search` for uniform fusion."""
        assert self.bm25 is not None
        t0 = time.perf_counter()
        hits = self.bm25.search(query, top_k=top_k)
        out = []
        for i, score in hits:
            row = dict(self.rows[i])
            row["bm25_score"] = score
            # Fusion is rank-based, but downstream aggregation reads `similarity`.
            # Rows found only by BM25 have no cosine, so seed it at 0.0 rather
            # than inventing a comparable value.
            row.setdefault("similarity", 0.0)
            out.append(row)
        return out, (time.perf_counter() - t0) * 1000.0

    def search_hybrid(
        self, query: str, top_k: int = STAGE1_K
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Dense + lexical, fused by RRF.

        Both arms retrieve top_k independently, so the fused pool is up to 2*top_k
        wide before truncation. That is the point: fusion can only promote a
        document that at least one arm surfaced.
        """
        t0 = time.perf_counter()
        vec_rows, _ = self.search(query, top_k=top_k)
        lex_rows, _ = self.search_lexical(query, top_k=top_k)

        # Carry the real cosine onto rows that both arms found, so the vector
        # score is not lost when a row arrives via the lexical list.
        cosine_by_key = {r["row_key"]: r["similarity"] for r in vec_rows}
        for r in lex_rows:
            if r["row_key"] in cosine_by_key:
                r["similarity"] = cosine_by_key[r["row_key"]]

        fused = fuse_result_rows(
            vector_rows=vec_rows,
            lexical_rows=lex_rows,
            id_key="row_key",
            top_k=top_k,
        )
        return fused, (time.perf_counter() - t0) * 1000.0


# ===========================================================================
# Ranking strategies
# ===========================================================================

def rank_by_score(rows: Sequence[Dict[str, Any]], score_key: str) -> List[str]:
    """Max-pool `score_key` per template and rank descending."""
    best: Dict[str, float] = {}
    for r in rows:
        t = r["t_id"]
        best[t] = max(best.get(t, -1e9), float(r.get(score_key, 0.0)))
    return [t for t, _ in sorted(best.items(), key=lambda kv: -kv[1])]


def rank_stage1_only(rows: Sequence[Dict[str, Any]]) -> List[str]:
    """Vector similarity, max-pooled per template."""
    return rank_by_score(rows, "similarity")


def rank_bm25_only(rows: Sequence[Dict[str, Any]]) -> List[str]:
    """BM25 score, max-pooled per template."""
    return rank_by_score(rows, "bm25_score")


def rank_rrf(rows: Sequence[Dict[str, Any]]) -> List[str]:
    """
    Fused rank, max-pooled per template.

    Rows arrive already carrying `rrf_score` from fuse_result_rows. Max-pooling
    matches the aggregation the production reranker uses, so the comparison
    isolates the retrieval change rather than confounding it with an
    aggregation change.
    """
    return rank_by_score(rows, "rrf_score")


_ACTION_KEYWORDS = (
    "create", "make", "add", "submit", "place", "generate", "process", "send",
    "post", "put", "delete", "update", "modify", "change", "set", "login",
    "logout", "register", "signup", "cancel", "refund", "please", "i want to",
)
_INFO_KEYWORDS = (
    "what", "how", "where", "when", "why", "which", "who", "show me", "list",
    "check", "did", "is", "has",
)


def _v1_auto_intent(query: str) -> str:
    """Faithful reproduction of v1 `_auto_detect_intent` (semantic_service:480)."""
    q = query.lower().strip()
    for kw in _ACTION_KEYWORDS:
        if kw in q:
            return "action"
    for kw in _INFO_KEYWORDS:
        if kw in q:
            return "info"
    return "action"


def rank_v1_heuristic(query: str, rows: Sequence[Dict[str, Any]]) -> List[str]:
    """
    The v1 shipped formula, reproduced exactly so the comparison is fair:
        0.7*avg_similarity + 0.15*avg_confidence + 0.15*intent_alignment
        then *1.1 (capped at 1.0) when avg_similarity >= 0.85
    Aggregation is MEAN, as v1 did.
    """
    intent = _v1_auto_intent(query)
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        buckets[r["t_id"]].append(r)

    scored: List[Tuple[str, float]] = []
    for t_id, group in buckets.items():
        avg_sim = statistics.fmean(r["similarity"] for r in group)
        avg_conf = statistics.fmean(r.get("confidence_score", 0.7) for r in group)
        matching = sum(1 for r in group if r.get("intent_type") == intent)
        intent_align = matching / len(group) if group else 0.0
        score = 0.7 * avg_sim + 0.15 * avg_conf + 0.15 * intent_align
        if avg_sim >= 0.85:
            score = min(score * 1.1, 1.0)
        scored.append((t_id, score))
    return [t for t, _ in sorted(scored, key=lambda kv: -kv[1])]


async def rank_cross_encoder(
    reranker: Any, query: str, rows: Sequence[Dict[str, Any]], strategy: str = "max"
) -> Tuple[List[str], float, bool]:
    outcome = await reranker.run(
        query=query, stage1_rows=rows, top_k=STAGE2_K, strategy=strategy
    )
    return (
        [t.t_id for t in outcome.templates],
        outcome.latency_ms,
        outcome.degraded,
    )


# ===========================================================================
# Metrics
# ===========================================================================

def hit_at_k(ranked: Sequence[str], expected: str, k: int) -> float:
    return 1.0 if expected in list(ranked)[:k] else 0.0


def reciprocal_rank(ranked: Sequence[str], expected: str, k: int = 5) -> float:
    for i, t in enumerate(list(ranked)[:k], start=1):
        if t == expected:
            return 1.0 / i
    return 0.0


def summarise(records: List[Dict[str, Any]], strategy: str) -> Dict[str, Any]:
    sel = [r for r in records if r["strategy"] == strategy]
    if not sel:
        return {}

    def agg(subset: List[Dict[str, Any]]) -> Dict[str, float]:
        if not subset:
            return {"n": 0, "hit@1": 0.0, "hit@3": 0.0, "hit@5": 0.0, "mrr@5": 0.0}
        return {
            "n": len(subset),
            "hit@1": statistics.fmean(r["hit@1"] for r in subset),
            "hit@3": statistics.fmean(r["hit@3"] for r in subset),
            "hit@5": statistics.fmean(r["hit@5"] for r in subset),
            "mrr@5": statistics.fmean(r["mrr@5"] for r in subset),
        }

    lat = sorted(r["latency_ms"] for r in sel)
    out: Dict[str, Any] = {
        "strategy": strategy,
        "overall": agg(sel),
        "by_tier": {t: agg([r for r in sel if r["tier"] == t]) for t in TIERS},
        "p50_ms": lat[len(lat) // 2],
        "p95_ms": lat[min(len(lat) - 1, int(len(lat) * 0.95))],
    }
    return out


# ===========================================================================
# Runner
# ===========================================================================

async def run(args: argparse.Namespace) -> int:
    print(f"\n{'=' * 74}\n NLPForge Routing Benchmark\n{'=' * 74}")

    embedder = build_embedder(args.embedder, args.model)
    index = UtteranceIndex(embedder)
    t0 = time.perf_counter()
    index.build()
    print(f"  embedder        : {embedder.name} (dim={embedder.dim})")
    print(f"  indexed rows    : {len(index.rows)} utterances / {len(API_TEMPLATES)} templates")
    print(f"  index build     : {(time.perf_counter() - t0) * 1000:.0f}ms")

    from app.nlp.cross_encoder_reranker import get_reranker

    reranker = get_reranker()
    ce_ready = await reranker.warm()
    print(f"  cross-encoder   : {'ready — ' + reranker.model_name if ce_ready else 'UNAVAILABLE (v2 rows will read as degraded)'}")

    cases = load_benchmark()
    print(f"  benchmark cases : {len(cases)}\n")

    records: List[Dict[str, Any]] = []
    stage1_recall_hits = 0
    hybrid_recall_hits = 0
    degraded_count = 0

    for n, case in enumerate(cases, start=1):
        query, expected, tier = case["query"], case["expected_api"], case["tier"]
        rows, s1_ms = index.search(query, top_k=STAGE1_K)
        lex_rows, lex_ms = index.search_lexical(query, top_k=STAGE1_K)
        hyb_rows, hyb_ms = index.search_hybrid(query, top_k=STAGE1_K)

        # Recall ceilings: what each Stage 1 hands to Stage 2. If hybrid recall
        # exceeds dense recall, fusion has surfaced templates dense retrieval
        # never had - a gain no reranker could have produced.
        if expected in {r["t_id"] for r in rows}:
            stage1_recall_hits += 1
        if expected in {r["t_id"] for r in hyb_rows}:
            hybrid_recall_hits += 1

        variants: List[Tuple[str, List[str], float, bool]] = [
            ("stage1_only", rank_stage1_only(rows), s1_ms, False),
            ("v1_heuristic", rank_v1_heuristic(query, rows), s1_ms, False),
            ("bm25_only", rank_bm25_only(lex_rows), lex_ms, False),
            ("hybrid_rrf", rank_rrf(hyb_rows), hyb_ms, False),
        ]
        ce_ranked, ce_ms, degraded = await rank_cross_encoder(reranker, query, rows)
        if degraded:
            degraded_count += 1
        variants.append(("v2_cross_encoder", ce_ranked, s1_ms + ce_ms, degraded))

        # The candidate: fuse first, then cross-encode the fused pool.
        hce_ranked, hce_ms, hce_degraded = await rank_cross_encoder(
            reranker, query, hyb_rows
        )
        variants.append(
            ("hybrid_rrf_cross_encoder", hce_ranked, hyb_ms + hce_ms, hce_degraded)
        )

        for strategy, ranked, latency, deg in variants:
            records.append(
                {
                    "id": case["id"],
                    "query": query,
                    "expected": expected,
                    "predicted": ranked[0] if ranked else None,
                    "tier": tier,
                    "cluster": cluster_of(expected),
                    "strategy": strategy,
                    "latency_ms": latency,
                    "degraded": deg,
                    "hit@1": hit_at_k(ranked, expected, 1),
                    "hit@3": hit_at_k(ranked, expected, 3),
                    "hit@5": hit_at_k(ranked, expected, 5),
                    "mrr@5": reciprocal_rank(ranked, expected, 5),
                }
            )

        if n % 30 == 0:
            print(f"  ...{n}/{len(cases)}")

    strategies = [
        "stage1_only",
        "bm25_only",
        "v1_heuristic",
        "hybrid_rrf",
        "v2_cross_encoder",
        "hybrid_rrf_cross_encoder",
    ]
    summaries = {s: summarise(records, s) for s in strategies}
    recall_at_k = stage1_recall_hits / len(cases)
    hybrid_recall = hybrid_recall_hits / len(cases)

    _print_report(summaries, recall_at_k, hybrid_recall, degraded_count, len(cases))

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "results.json").write_text(
        json.dumps(
            {
                "embedder": embedder.name,
                "reranker": reranker.model_name if ce_ready else None,
                "cases": len(cases),
                f"dense_recall@{STAGE1_K}": recall_at_k,
                f"hybrid_recall@{STAGE1_K}": hybrid_recall,
                "summaries": summaries,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (outdir / "per_query.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\n  wrote {outdir / 'results.json'} and {outdir / 'per_query.json'}")

    if args.markdown:
        Path(args.markdown).write_text(
            _markdown(summaries, recall_at_k, embedder.name,
                      reranker.model_name if ce_ready else "unavailable"),
            encoding="utf-8",
        )
        print(f"  wrote {args.markdown}")

    if args.fail_under is not None:
        gate = args.gate_strategy
        if gate not in summaries or not summaries[gate]:
            print(f"\n  FAIL: unknown --gate-strategy {gate!r}")
            return 1
        got = summaries[gate]["overall"]["hit@1"]
        if got < args.fail_under:
            print(f"\n  FAIL: {gate} Hit@1 {got:.3f} < threshold {args.fail_under:.3f}")
            return 1
        print(f"\n  PASS: {gate} Hit@1 {got:.3f} >= threshold {args.fail_under:.3f}")
    return 0


def _fmt_row(label: str, m: Dict[str, float]) -> str:
    if not m or not m.get("n"):
        return f"  {label:<20} —"
    return (
        f"  {label:<20} {m['hit@1']:>7.3f} {m['hit@3']:>8.3f} "
        f"{m['hit@5']:>8.3f} {m['mrr@5']:>8.3f}   (n={int(m['n'])})"
    )


def _print_report(
    summaries: Dict[str, Dict[str, Any]],
    recall: float,
    hybrid_recall: float,
    degraded: int,
    total: int,
) -> None:
    print(f"\n{'=' * 74}\n RESULTS\n{'=' * 74}")
    print(f"\n  Stage 1 recall@{STAGE1_K}: {recall:.3f}  "
          f"<- the ceiling Stage 2 can never exceed")
    print(f"  hybrid recall@{STAGE1_K}: {hybrid_recall:.3f}  "
          f"({hybrid_recall - recall:+.3f} from adding the lexical arm)")
    if degraded:
        print(f"  WARNING: {degraded}/{total} queries ran DEGRADED "
              f"(cross-encoder unavailable) — v2 numbers are not meaningful.")

    print(f"\n{'  OVERALL':<22}{'Hit@1':>7}{'Hit@3':>9}{'Hit@5':>9}{'MRR@5':>9}")
    print("  " + "-" * 62)
    for s, summ in summaries.items():
        if summ:
            print(_fmt_row(s, summ["overall"]))
            print(f"  {'':<20} p50={summ['p50_ms']:.1f}ms  p95={summ['p95_ms']:.1f}ms")

    for tier in TIERS:
        print(f"\n{'  TIER: ' + tier.upper():<22}{'Hit@1':>7}{'Hit@3':>9}{'Hit@5':>9}{'MRR@5':>9}")
        print("  " + "-" * 62)
        for s, summ in summaries.items():
            if summ:
                print(_fmt_row(s, summ["by_tier"][tier]))

    base = summaries["stage1_only"]["overall"]["hit@1"]
    v1 = summaries["v1_heuristic"]["overall"]["hit@1"]
    v2 = summaries["v2_cross_encoder"]["overall"]["hit@1"]
    hard_base = summaries["stage1_only"]["by_tier"]["hard_negative"]["hit@1"]
    hard_v2 = summaries["v2_cross_encoder"]["by_tier"]["hard_negative"]["hit@1"]

    print(f"\n{'=' * 74}\n VERDICT\n{'=' * 74}")
    print(f"  v1 heuristic vs raw vector : {v1 - base:+.3f} Hit@1")
    print(f"    -> v1 re-sorted Stage 1's own scores; near-zero delta is expected")
    print(f"  v2 cross-encoder vs vector : {v2 - base:+.3f} Hit@1")
    print(f"  v2 on HARD NEGATIVES       : {hard_v2 - hard_base:+.3f} Hit@1 "
          f"({hard_base:.3f} -> {hard_v2:.3f})")


def _markdown(
    summaries: Dict[str, Dict[str, Any]], recall: float, embedder: str, reranker: str
) -> str:
    lines = [
        "### Routing Benchmark",
        "",
        f"`{len(load_benchmark())}` held-out queries · `{len(API_TEMPLATES)}` API templates · "
        f"embedder `{embedder}` · reranker `{reranker}`",
        "",
        f"Stage 1 recall@{STAGE1_K}: **{recall:.3f}**",
        "",
        "| Strategy | Hit@1 | Hit@3 | MRR@5 | p50 | p95 |",
        "|---|---|---|---|---|---|",
    ]
    for s, summ in summaries.items():
        if not summ:
            continue
        o = summ["overall"]
        lines.append(
            f"| `{s}` | {o['hit@1']:.3f} | {o['hit@3']:.3f} | {o['mrr@5']:.3f} | "
            f"{summ['p50_ms']:.1f}ms | {summ['p95_ms']:.1f}ms |"
        )
    lines += ["", "**Hit@1 by difficulty tier**", "",
              "| Strategy | " + " | ".join(t for t in TIERS) + " |",
              "|---|" + "---|" * len(TIERS)]
    for s, summ in summaries.items():
        if not summ:
            continue
        cells = " | ".join(f"{summ['by_tier'][t]['hit@1']:.3f}" for t in TIERS)
        lines.append(f"| `{s}` | {cells} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description="NLPForge routing benchmark")
    p.add_argument("--embedder", choices=["tfidf", "onnx", "ollama"], default="tfidf")
    p.add_argument("--model", default="nomic-embed-text", help="ollama model name")
    p.add_argument("--outdir", default=str(Path(__file__).parent / "results"))
    p.add_argument("--markdown", help="write a README-ready markdown table here")
    p.add_argument("--fail-under", type=float,
                   help="exit 1 if the gated strategy Hit@1 falls below this")
    p.add_argument("--gate-strategy", default="stage1_only",
                   help="which strategy --fail-under gates on; defaults to the shipped config (dense-only, reranker off)")
    args = p.parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
