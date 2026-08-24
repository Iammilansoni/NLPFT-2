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
     Stage 2  PRECISION  ───┤  cross-encoder rerank → top template
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
Ollama, so it runs in CI on every push.

```bash
python evals/run_eval.py --fail-under 0.70
```

`embedder tfidf-char3` · `reranker ms-marco-MiniLM-L-12-v2` · `STAGE1_TOP_K=25`
· Stage 1 recall@25 **0.978**

| Strategy | Hit@1 | Hit@3 | MRR@5 | p50 | p95 |
|---|---|---|---|---|---|
| `stage1_only` — vector similarity only | 0.617 | 0.861 | 0.740 | 0.3ms | 0.4ms |
| `v1_heuristic` — what v1 shipped | 0.444 | 0.717 | 0.581 | 0.3ms | 0.4ms |
| **`v2_cross_encoder`** — current | **0.728** | **0.906** | **0.823** | 122ms | 176ms |

Accuracy figures are deterministic and reproduce exactly. Latency is CPU-bound
and machine-dependent — 120–265ms p50 observed across runs on a laptop.

**Hit@1 by difficulty tier**

| Strategy | direct | paraphrase | colloquial | hard_negative |
|---|---|---|---|---|
| `stage1_only` | 0.950 | 0.400 | 0.825 | 0.400 |
| `v1_heuristic` | 0.700 | 0.300 | 0.575 | 0.275 |
| `v2_cross_encoder` | 0.950 | **0.650** | 0.825 | **0.525** |

### What the benchmark found

**v1's reranker was actively harmful.** It scored **0.444 against a 0.617
baseline** — 17 points *worse* than doing nothing. It computed
`0.7·avg_similarity + 0.15·avg_confidence + 0.15·intent_alignment`, where
`avg_similarity` was Stage 1's own cosine score. It could only re-sort Stage 1's
ordering, and the `intent_alignment` term (keyword substring matching, where
`"please"` implied `action`) injected noise uncorrelated with relevance.
Deleting it outright would have improved routing.

**Every routing error is a precision failure.** Stage 1 recall@50 is **1.000** —
the correct template is *always* retrieved. That is what justifies spending
latency on reranking rather than on better recall.

**Deeper retrieval is not better.** k=50 has perfect recall and *worse* Hit@1
(0.717) than k=25 (0.728), at double the latency. More marginal candidates give
the cross-encoder more chances to be confidently wrong. Recall is the ceiling,
not the objective.

**The 4MB reranker is not a substitute.** `ms-marco-TinyBERT-L-2-v2` is 6×
faster and scores 0.400 on hard negatives — identical to no reranking at all. It
reorders easy queries and cannot discriminate sibling endpoints.

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
                    │ Stage 2 · PRECISION       k=5           │
                    │ FlashRank ms-marco-MiniLM-L-12-v2       │
                    │ cross-encode(query, utterance)          │
                    │ → aggregate to template by MAX          │
                    └────────────────┬────────────────────────┘
                    ┌────────────────▼────────────────────────┐
                    │ Stage 3 · EXTRACTION                    │
                    │ schema-constrained decode               │
                    │ → Pydantic validate → repair retry      │
                    │ Redis-backed circuit breaker            │
                    └─────────────────────────────────────────┘
```

### Design decisions worth explaining

**Cross-encode utterances, not template descriptions.** Templates carry 500+ word
descriptions that exceed the 512-token window and sit off the distribution
`ms-marco` was trained on. Retrieved rows carry short natural-language text —
exactly the passage shape the model expects.

**Aggregate rows→template by MAX, not mean.** A template with one perfect match
among ten mediocre ones is a better route than one with eleven lukewarm matches.
Mean-pooling (v1's behaviour) ranks it lower. This was a larger accuracy lever
than the cross-encoder itself.

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

- **Benchmark numbers are TF-IDF character-trigram**, the zero-dependency CI
  baseline. Absolute values shift under `--embedder onnx`. The *relative ordering*
  of the three strategies is the finding; the absolute Hit@1 is not a production
  figure.
- **20 templates is a small catalogue.** Hit@1 will fall as it grows. Re-run
  before quoting numbers at a different scale.
- **Reranking dominates latency** — 120–265ms p50 on CPU, unbatched, on a laptop,
  against sub-millisecond vector search. This is the strongest argument for the
  Stage 0 cache, and the main reason cloud mode is worth its complexity.
- **Hit@1 on hard negatives is 0.525.** Better than the 0.400 baseline, not
  solved. Sibling endpoints that differ by *authentication state* rather than
  vocabulary remain the dominant error class.
- **Hybrid lexical + vector retrieval with RRF is designed but not built.** It is
  the next accuracy lever, and the eval harness is in place to measure it.
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
