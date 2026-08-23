# NLPForge Routing Benchmark

Measures how reliably natural language is routed to the correct API template, and
quantifies exactly what Stage 2 contributes over Stage 1 alone.

## Run it

```bash
python evals/run_eval.py                          # tfidf embedder — zero extra deps
python evals/run_eval.py --embedder onnx          # bge-small-en-v1.5 (cloud mode)
python evals/run_eval.py --embedder ollama        # nomic-embed-text (local mode)
python evals/run_eval.py --markdown out.md        # README-ready table
python evals/run_eval.py --fail-under 0.70        # CI gate on Hit@1
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
`Password_Reset_Confirm`, and `Password_Change` share nearly every content word.
Bi-encoder recall surfaces all three; bi-encoder *precision* routinely picks the
wrong one. That is exactly what a cross-encoder is for.

### Strategies compared

| Strategy | What it is |
|---|---|
| `stage1_only` | Vector similarity, max-pooled per template. The honest baseline. |
| `v1_heuristic` | The formula NLPForge v1 actually shipped, reproduced faithfully. |
| `v2_cross_encoder` | FlashRank `ms-marco-MiniLM-L-12-v2`, max-pooled per template. |

---

## Results

`180` held-out queries · `20` templates · embedder `tfidf-char3` · reranker
`ms-marco-MiniLM-L-12-v2` · `STAGE1_TOP_K=25`

Stage 1 recall@25: **0.978**

| Strategy | Hit@1 | Hit@3 | MRR@5 | p50 | p95 |
|---|---|---|---|---|---|
| `stage1_only` | 0.617 | 0.861 | 0.740 | 0.4ms | 0.7ms |
| `v1_heuristic` | 0.444 | 0.717 | 0.581 | 0.4ms | 0.7ms |
| **`v2_cross_encoder`** | **0.728** | **0.906** | **0.823** | 264.6ms | 370.1ms |

**Hit@1 by tier**

| Strategy | direct | paraphrase | colloquial | hard_negative |
|---|---|---|---|---|
| `stage1_only` | 0.950 | 0.400 | 0.825 | 0.400 |
| `v1_heuristic` | 0.700 | 0.300 | 0.575 | 0.275 |
| `v2_cross_encoder` | 0.950 | **0.650** | 0.825 | **0.525** |

### Findings

**1. The v1 "reranker" was actively harmful — not merely inert.**

The audit predicted v1's formula could not *improve* on Stage 1, since
`avg_similarity` was Stage 1's own cosine score. Measurement shows worse: v1
scored **0.444 Hit@1 against a 0.617 baseline, a 17-point regression.** The
`intent_alignment` term (keyword substring matching, where `"please"` implies
`action`) and mean-aggregation both inject noise uncorrelated with relevance.
Removing v1's Stage 2 entirely would have improved routing.

**2. All routing errors are precision failures, not recall failures.**

Stage 1 recall@50 is **1.000** — the correct template is *always* retrieved. Every
error is the ranker choosing wrongly among candidates it already had. This says
unambiguously that reranking, not better recall, is where effort belongs.

**3. Deeper over-retrieval is not better.**

| `STAGE1_TOP_K` | recall | Hit@1 | p50 |
|---|---|---|---|
| 15 | 0.972 | 0.717 | ~160ms |
| **25** | 0.978 | **0.728** | **265ms** |
| 50 | **1.000** | 0.717 | 482ms |

k=50 has perfect recall and *worse* Hit@1 than k=25. More marginal candidates give
the cross-encoder more chances to be confidently wrong. **Recall is the ceiling,
not the objective.** k=25 is the default.

**4. The 4MB reranker is not a viable substitute.**

| Reranker | Hit@1 | hard_negative | p50 |
|---|---|---|---|
| `ms-marco-MiniLM-L-12-v2` (~34MB) | 0.717 | **0.525** | 482ms |
| `ms-marco-TinyBERT-L-2-v2` (~4MB) | 0.650 | 0.400 | **77ms** |

TinyBERT is 6× faster and surrenders **the entire hard-negative gain** (0.400 —
identical to no reranking at all). It reorders easy queries and cannot discriminate
siblings. If cold-start size forces TinyBERT, the honest description is
"vector routing with cosmetic reranking."

### Caveats

- These are **TF-IDF character-trigram** numbers, the zero-dependency baseline.
  Absolute values will shift with `--embedder onnx`; the *relative* ordering of
  strategies is the finding.
- 20 templates is a small catalogue. Hit@1 will fall as the catalogue grows —
  re-run before quoting numbers at a different scale.
- `p50=265ms` is measured on CPU, unbatched, on a developer laptop. This is a real
  production concern, not a footnote: it is the dominant cost in the pipeline and
  the strongest argument for the Stage 0 semantic cache.

## Reproducing

```bash
py -3.11 -m venv .venv-eval
./.venv-eval/Scripts/python -m pip install numpy flashrank
./.venv-eval/Scripts/python evals/run_eval.py
```

Outputs land in `evals/results/` — `results.json` (aggregates) and
`per_query.json` (every query, prediction, and score, for error analysis).
