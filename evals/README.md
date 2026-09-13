# NLPForge Routing Benchmark

Measures how reliably natural language is routed to the correct API template, and
quantifies exactly what Stage 2 contributes over Stage 1 alone.

## Run it

```bash
python evals/run_eval.py --embedder onnx          # bge-small-en-v1.5 — the reported numbers
python evals/run_eval.py                          # tfidf smoke mode, no model download
python evals/run_eval.py --embedder ollama        # nomic-embed-text (local mode)
python evals/run_eval.py --markdown out.md        # README-ready table
python evals/run_eval.py --gate-strategy stage1_only --fail-under 0.78   # CI gate
```

No PostgreSQL, Redis, or running API required — the harness builds its own
in-memory index, so it runs in CI on every push.

## Design

| File | Purpose |
|---|---|
| `api_surface.py` | 20 API templates + 100 indexed utterances, grouped into confusion clusters |
| `benchmark_queries.py` | 180 held-out labeled queries across 4 difficulty tiers |
| `run_eval.py` | Index, three ranking strategies, metrics, reporting |

**Exact cosine, not ANN.** Stage 1 uses brute-force cosine rather than HNSW.
ANN recall loss and reranker quality are different failure modes; mixing them makes
the numbers uninterpretable. Recall/latency for HNSW is a separate experiment.

**Held-out queries.** Nothing in `benchmark_queries.py` appears in the indexed
utterances. The model never sees these strings at index time.

### Difficulty tiers

| Tier | n | What it measures |
|---|---|---|
| `direct` | 40 | Plain phrasing. A floor — failure here means something is broken. |
| `paraphrase` | 60 | Same intent, minimal lexical overlap. Semantic generalisation. |
| `colloquial` | 40 | Terse, slangy, typo'd. Robustness to real user input. |
| `hard_negative` | 40 | Lexically closest to a **sibling** template, semantically belongs to the labeled one. |

Hard negatives are the tier that matters. `Password_Reset_Request`,
`Password_Reset_Confirm`, and `Password_Change` share nearly every content word
and differ by *authentication state*, not vocabulary. Recall surfaces all three;
precision routinely picks the wrong one.

This tier was built expecting a cross-encoder to be the answer. It was not — see
Finding 2. It remains the hardest tier for every strategy tested, and the clearest
target for future work.

### Strategies compared

| Strategy | What it is |
|---|---|
| `stage1_only` | Dense vector similarity, max-pooled per template. The baseline — and the shipped default. |
| `bm25_only` | BM25-Okapi lexical retrieval, max-pooled per template. |
| `hybrid_rrf` | Dense + BM25 fused by Reciprocal Rank Fusion (k=60). |
| `v2_cross_encoder` | Dense → FlashRank `ms-marco-MiniLM-L-12-v2` rerank. |
| `hybrid_rrf_cross_encoder` | Fused pool → cross-encoder rerank. |
| `v1_heuristic` | The formula NLPForge v1 actually shipped, reproduced faithfully. |

The harness forces `RERANKER_ENABLED=true` regardless of the shipped default,
because its job is to *measure* the reranker even though production runs without
it.

---

## Results

`180` held-out queries · `20` templates · `STAGE1_TOP_K=25` ·
embedder **`bge-small-en-v1.5`** · dense recall@25 **1.000**

| Strategy | Hit@1 | Hit@3 | MRR@5 | Ships? |
|---|---|---|---|---|
| **`stage1_only`** | **0.822** | **0.983** | **0.896** | default |
| `hybrid_rrf` | 0.806 | 0.956 | 0.880 | available |
| `v2_cross_encoder` | 0.739 | 0.944 | 0.836 | off |
| `bm25_only` | 0.600 | 0.861 | 0.727 | — |
| `v1_heuristic` | 0.589 | 0.850 | 0.712 | removed |

**Hit@1 by tier**

| Strategy | direct | paraphrase | colloquial | hard_negative |
|---|---|---|---|---|
| `stage1_only` | 0.950 | **0.900** | 0.800 | 0.600 |
| `hybrid_rrf` | **1.000** | 0.717 | **0.900** | **0.650** |
| `v2_cross_encoder` | 0.975 | 0.683 | 0.800 | 0.525 |
| `bm25_only` | 0.900 | 0.417 | 0.700 | 0.475 |
| `v1_heuristic` | 0.750 | 0.500 | 0.600 | 0.400 |

### Findings

**1. v1's reranker was actively harmful — not merely inert.**

The audit predicted v1's formula could not *improve* on Stage 1, since
`avg_similarity` was Stage 1's own cosine score. Measurement showed worse: v1
scored **0.589 against a 0.822 baseline**, a 23-point regression. The
`intent_alignment` term (keyword substring matching, where `"please"` implies
`action`) and mean-aggregation both inject noise uncorrelated with relevance.

**2. The cross-encoder is also a regression — and the benchmark itself was
initially at fault.**

The first version of this harness had only a char-trigram TF-IDF embedder.
Against that weak baseline the cross-encoder measured **+0.111 Hit@1**, and it
shipped on that basis.

Re-run against the production embedder, it is **−0.083** (0.822 → 0.739). It
loses at every retrieval depth, so it is not a k-tuning artefact:

| `STAGE1_TOP_K` | dense only | + cross-encoder |
|---|---|---|
| 5 | 0.822 | 0.756 |
| 10 | 0.822 | 0.750 |
| 25 | 0.822 | 0.739 |

`ms-marco-MiniLM` is trained on web-search queries against prose passages. This
corpus is short imperative commands matched against short utterances — off
distribution for it, and exactly what `bge-small` is trained for.

The methodological lesson generalises: **a reranker measured against a weak
retriever will always look good.** TF-IDF left headroom to recover; a competent
embedder leaves none. Benchmark against what you actually ship.

**3. Every routing error is a precision failure.**

Dense recall@25 is **1.000** — the correct template is always retrieved. All
remaining headroom is in ranking, none in recall.

**4. Hybrid retrieval wins the hardest tier but not overall.**

BM25 fused by RRF lifts hard negatives 0.600 → **0.650** and direct queries to a
perfect **1.000**, for sub-millisecond cost. But it costs 0.822 → 0.806 overall,
diluting the paraphrase tier where dense is strongest (0.900 → 0.717). On n=180
that delta is within noise, so it ships available but not default.

**5. The 4MB reranker is not a viable substitute** (measured on tfidf, where the
cross-encoder still had a positive delta): `ms-marco-TinyBERT-L-2-v2` is 6×
faster and surrenders the entire hard-negative gain.

### Caveats

- **Conclusions are embedder-specific.** The cross-encoder result reversed sign
  between tfidf and bge-small. Everything reported here holds for
  `bge-small-en-v1.5` and must be re-measured for any other embedder. The `tfidf`
  mode exists for dependency-free smoke runs; its absolute numbers are not
  production figures.
- **n=180 over 20 templates.** Deltas under ~0.03 are indistinguishable from
  noise — which is precisely why `hybrid_rrf` is not shipped as the default
  despite winning the hard-negative tier. Hit@1 will fall as the catalogue grows.
- **Exact cosine, not ANN.** Stage 1 here is brute-force, so these numbers isolate
  ranking quality from HNSW recall loss. Production uses pgvector HNSW, whose
  recall/latency curve is a separate experiment.
- **BM25 here is in-memory** and does not scale to a multi-tenant corpus. The
  production lexical arm would be PostgreSQL `tsvector`/`ts_rank_cd`, which is a
  different ranking function — so the hybrid numbers predict direction, not exact
  magnitude.

## Reproducing

```bash
py -3.11 -m venv .venv-eval
./.venv-eval/Scripts/python -m pip install numpy flashrank fastembed
./.venv-eval/Scripts/python evals/run_eval.py --embedder onnx
```

Outputs land in `evals/results/` — `results.json` (aggregates) and
`per_query.json` (every query, prediction, and score, for error analysis).
