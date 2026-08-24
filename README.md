<div align="center">

# NLPForge

### Semantic API Router & Structured Extraction Harness

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.123+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![pgvector](https://img.shields.io/badge/pgvector-HNSW-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![CI](https://img.shields.io/github/actions/workflow/status/Iammilansoni/NLPFT-2/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/Iammilansoni/NLPFT-2/actions)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**Routes natural language to the right API endpoint, then extracts a
schema-valid request body — deterministically, and with the accuracy measured.**

</div>

---

## What this is

NLPForge is the **deterministic routing layer that sits beneath an LLM agent**,
not the agent itself.

Give it a sentence. It picks the correct API template out of a catalogue, fills
in the request body against that template's JSON Schema, and hands back
structured, executable output:

```
  "authenticate with email dana@shop.io and password Passw0rd"
                            │
     Stage 1  RECALL     ───┤  bi-encoder → pgvector HNSW, k=25
     Stage 2  RANKING    ───┤  max-pool rows → top template
     Stage 3  EXTRACTION ───┤  schema-constrained decode → Pydantic validate
                            ▼
  {
    "api_name": "User_Login",
    "endpoint": "/auth/login",
    "method": "POST",
    "confidence_score": 0.9137,
    "extracted_request_body": {
      "email": "dana@shop.io",
      "password": "Passw0rd"
    },
    "degraded": false
  }
```

**What it is not.** There is no planning loop, no multi-step tool execution, no
conversation. It resolves one utterance to one endpoint. That constraint is the
point: agents are unreliable at tool selection precisely because routing is
usually left to a prompt. This makes routing a measurable retrieval problem
instead.

---

## Routing benchmark

Accuracy is measured, not asserted. `evals/` holds **180 held-out queries** over
**20 API templates** in four difficulty tiers. It needs no PostgreSQL, Redis or
Ollama, so it runs in CI on every push and gates merges.

```bash
python evals/run_eval.py --embedder onnx          # the numbers below
python evals/run_eval.py                          # tfidf smoke mode, no downloads
```

`embedder bge-small-en-v1.5` · `STAGE1_TOP_K=25` · dense recall@25 **1.000**

| Strategy | Hit@1 | Hit@3 | MRR@5 | Ships? |
|---|---|---|---|---|
| **`stage1_only`** — dense vector only | **0.822** | **0.983** | **0.896** | ✅ **default** |
| `hybrid_rrf` — dense + BM25 fused | 0.806 | 0.956 | 0.880 | available |
| `v2_cross_encoder` — + cross-encoder | 0.739 | 0.944 | 0.836 | off by default |
| `bm25_only` — lexical only | 0.600 | 0.861 | 0.727 | — |
| `v1_heuristic` — what v1 shipped | 0.589 | 0.850 | 0.712 | removed |

**Hit@1 by difficulty tier**

| Strategy | direct | paraphrase | colloquial | hard_negative |
|---|---|---|---|---|
| `stage1_only` | 0.950 | **0.900** | 0.800 | 0.600 |
| `hybrid_rrf` | **1.000** | 0.717 | **0.900** | **0.650** |
| `v2_cross_encoder` | 0.975 | 0.683 | 0.800 | 0.525 |

Accuracy is deterministic and reproduces exactly. Latency: dense retrieval is
sub-millisecond; the cross-encoder adds 120–265ms p50 on CPU.

### What the benchmark found

**v1's reranker was actively harmful.** It scored **0.589 against a 0.822
baseline** — 23 points *worse* than doing nothing. It computed
`0.7·avg_similarity + 0.15·avg_confidence + 0.15·intent_alignment`, where
`avg_similarity` was Stage 1's own cosine score. It could only re-sort Stage 1's
ordering, and the `intent_alignment` term (keyword substring matching, where
`"please"` implied `action`) injected noise uncorrelated with relevance.

**The cross-encoder was also a regression — and finding that required fixing the
benchmark first.** Measured against a char-trigram TF-IDF baseline it looked like
a clear +0.111 Hit@1 win, and it shipped on that basis. Re-measured against the
actual production embedder it is **−0.083** (0.822 → 0.739), losing at every
retrieval depth:

| `STAGE1_TOP_K` | dense only | + cross-encoder |
|---|---|---|
| 5 | 0.822 | 0.756 |
| 10 | 0.822 | 0.750 |
| 25 | 0.822 | 0.739 |

Not a tuning problem. `ms-marco-MiniLM` is trained on web-search queries against
prose passages; this corpus is short imperative commands matched against short
utterances, which is off-distribution for it. `bge-small` is trained for exactly
that shape and wins outright. **The earlier gain was an artefact of a weak
baseline** — TF-IDF left room to recover; a good embedder leaves none.

`RERANKER_ENABLED` therefore defaults to `false`. The code, the benchmark arm and
the measurement all remain, so the decision is re-checkable against any new
embedder rather than inherited on faith.

**Hybrid retrieval wins the hardest tier but not overall.** BM25 fused by
Reciprocal Rank Fusion takes hard negatives from 0.600 → **0.650** and direct
queries to a perfect 1.000, at sub-millisecond cost — but costs 0.822 → 0.806
overall, because it dilutes the paraphrase tier where dense retrieval is strongest
(0.900 → 0.717). On n=180 that overall delta is within noise. Shipped as
available, not as default, on the principle that an unproven gain does not become
a default.

**Every routing error is a precision failure.** Dense recall@25 is **1.000** —
the correct template is always retrieved. No amount of recall tuning can help;
all remaining headroom is in ranking.

Full methodology, tier definitions and caveats: **[`evals/README.md`](evals/README.md)**

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
  NL query ─────────▶ Stage 0 · semantic cache (Redis)        │──hit──▶ response
                    └────────────────┬────────────────────────┘
                                     │ miss
                    ┌────────────────▼────────────────────────┐
                    │ Stage 1 · RECALL          k=25          │
                    │ embedder → pgvector HNSW                │
                    │ RLS + hnsw.iterative_scan               │
                    └────────────────┬────────────────────────┘
                    ┌────────────────▼────────────────────────┐
                    │ Stage 2 · RANKING                       │
                    │ max-pool utterance rows → template      │
                    │                                         │
                    │ optional, OFF by default, measured:     │
                    │   · BM25 + RRF fusion   (hybrid)        │
                    │   · FlashRank cross-encoder  (−0.083)   │
                    └────────────────┬────────────────────────┘
                    ┌────────────────▼────────────────────────┐
                    │ Stage 3 · EXTRACTION                    │
                    │ schema-constrained decode               │
                    │ → Pydantic validate → repair retry      │
                    │ Redis-backed circuit breaker            │
                    └─────────────────────────────────────────┘
```

### Design decisions worth explaining

**Aggregate rows→template by MAX, not mean.** A template with one perfect match
among ten mediocre ones is a better route than one with eleven lukewarm matches.
Mean-pooling (v1's behaviour) ranks it lower. This turned out to be a larger
accuracy lever than the cross-encoder — which was negative.

**Optional ranking stages stay in the tree, switched off.** The cross-encoder and
the BM25/RRF hybrid are both fully implemented, both wired into the benchmark as
comparison arms, and both default to off because measurement said so. Deleting
them would discard the ability to re-check that decision when the embedder
changes; enabling them by default would repeat the mistake of shipping an
unmeasured assumption. `RERANKER_ENABLED=true` and `VECTOR_BACKEND` make either
one a config change, not a code change.

**Tenant isolation is enforced by PostgreSQL, not by application code.** v1 relied
on 32+ hand-written `u_id ==` filters across the routers; one omission is a
cross-tenant leak. v2 uses Row-Level Security with a tenant-scoped session.

Two non-obvious things that make RLS work, both handled in `app/core/tenancy.py`:

- **`SET LOCAL`, never `SET`.** The session pool reuses connections. A plain `SET`
  persists the tenant GUC past the request, and the next request — for a
  *different* tenant — inherits it. That turns the security feature into the
  leak. `SET LOCAL` is transaction-scoped, so it requires an explicit
  transaction.
- **`hnsw.iterative_scan`.** An HNSW scan returns `ef_search` candidates and RLS
  filters them *afterwards*. A tenant owning 2% of rows can get **zero** results
  from a top-50 scan — no error, just silent recall collapse. Iterative scan
  keeps pulling until it has enough post-filter rows.

**Circuit breaker state lives in Redis.** The API and N Celery workers are separate
processes. An in-process breaker would let the API trip correctly while workers
keep hammering the same dead dependency. Breaker state is a property of the
dependency, not of the observer.

**Failure is reported, never swallowed.** v1 returned `{}` when extraction failed
*and* when a query genuinely had no slots — byte-identical. Every response now
carries `degraded` and `degraded_reason`.

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI (async) | — |
| Vectors | **PostgreSQL + pgvector HNSW** | RLS cannot span a Redis boundary; one storage engine, one tenancy model |
| Reranker | FlashRank `ms-marco-MiniLM-L-12-v2` (~34MB ONNX) | Measured best accuracy/latency point |
| Embeddings | `bge-small-en-v1.5` ONNX (cloud) / Ollama (local) | Selected by `EXECUTION_MODE` |
| Extraction LLM | Ollama (local) / Gemini Flash, Groq (cloud) | — |
| Redis | cache, rate limiting, JWT denylist, breaker state | *Not* vectors |
| Queue | Celery | Dataset generation |
| Frontend | Next.js 16 | — |

Redis HNSW from v1 is retained behind `VECTOR_BACKEND=redis` as a benchmark arm,
so the pgvector migration stays measurable rather than assumed.

---

## Quick start

### Local — zero API keys, fully offline

```bash
git clone https://github.com/Iammilansoni/NLPFT-2.git
cd NLPFT-2
cp Backend/.env.example .env      # POSTGRES_PASSWORD and SECRET_KEY are required
docker compose up -d
docker compose exec backend python scripts/seed_demo.py
```

`seed_demo.py` creates a sandbox tenant with the 20 benchmark templates already
embedded, so the pipeline is queryable immediately. Open http://localhost:3000
and sign in with the credentials the seed script prints.

### Cloud — serverless MVP

No Ollama container: embeddings run in-process via ONNX, inference uses a hosted
API. Fits Neon + Fly.io + Vercel free tiers.

```bash
EXECUTION_MODE=cloud
```

Full walkthrough and cost breakdown: **[`DEPLOYMENT.md`](DEPLOYMENT.md)**

---

## Testing

```bash
cd Backend
pytest                                     # 115 tests
python ../evals/run_eval.py                # routing benchmark
python scripts/backfill_redis_to_pgvector.py --dry-run
```

CI runs lint, the unit suite, the frontend build, and the routing benchmark as a
merge gate.

---

## Version history

| Tag / branch | What it is |
|---|---|
| **`v1.0-internship`** | Internship delivery, Sep 2025 – Feb 2026. Two-stage retrieval prototype: FastAPI + Redis HNSW + Celery + Ollama, 8 LLM providers, Docker Compose. |
| **`v2-ai-harness`** | Current. Real cross-encoder, measured routing, pgvector + RLS, dual runtime, structured extraction. |

`v1.0-internship` is preserved deliberately. The measured regression it exhibits
(`v1_heuristic` at 0.444 vs a 0.617 baseline) is reproducible from that tag, and
the delta is the point of the rewrite.

---

## Known limitations

Stated plainly, because the previous README's central claim did not survive
contact with its own code.

- **Benchmark conclusions are embedder-specific.** The cross-encoder result
  reversed sign between two embedders. Any claim here holds for
  `bge-small-en-v1.5` and must be re-measured for another. `--embedder tfidf`
  remains as a zero-dependency smoke mode; its *absolute* numbers are not
  production figures.
- **20 templates is a small catalogue**, and n=180 makes deltas under ~0.03
  indistinguishable from noise — which is why the hybrid arm is not shipped as
  default. Hit@1 will fall as the catalogue grows. Re-run before quoting numbers
  at a different scale.
- **Hit@1 on hard negatives is 0.600** (0.650 with hybrid). Sibling endpoints
  that differ by *authentication state* rather than vocabulary — reset-request vs
  reset-confirm vs change-password — remain the dominant error class, and no
  ranking strategy tested here solves them.
- **A reranker trained on this distribution has not been tried.** The failure of
  `ms-marco` is a domain-mismatch result, not evidence that reranking cannot
  help. Fine-tuning a cross-encoder on the generated dataset is the obvious next
  experiment, and the harness will measure it.
- **The frontend is functional, not polished.** Effort went to the retrieval
  pipeline and the data layer.

---

## Project layout

```
Backend/
  app/
    nlp/cross_encoder_reranker.py     Stage 2 reranking
    nlp/semantic_dedup.py             generation-time dedup
    core/tenancy.py                   RLS session + HNSW scan tuning
    core/circuit_breaker.py           Redis-backed breaker
    core/runtime.py                   EXECUTION_MODE adapter
    services/pgvector_store.py        Stage 1 recall
    services/structured_extraction_service.py   Stage 3
    repositories/                     SQL out of the routers
  scripts/seed_demo.py                one-click sandbox tenant
evals/                                180-query routing benchmark
DEPLOYMENT.md                         local + cloud deployment
```

---

## License

MIT — see [LICENSE](LICENSE).
