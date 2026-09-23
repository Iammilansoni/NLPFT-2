<div align="center">

# NLPForge

**Turn a sentence into a validated API call.**

A semantic API router: vector retrieval picks the right endpoint from your API catalogue, and a
schema-constrained LLM extracts a request body that validates against that endpoint's JSON Schema.
Routing accuracy is measured on a held-out benchmark in CI.

[Architecture](docs/ARCHITECTURE.md) · [Run it locally](#getting-started) · [Benchmark](#measured-results) · [Deployment](DEPLOYMENT.md)

![NLPForge demo: a request is routed to Refund_Order and its body extracted; a request missing a password is reported, not invented](docs/demo.gif)

FastAPI · PostgreSQL + pgvector · Ollama (nomic-embed-text, llama3.2) · Pydantic · Celery + Redis · Next.js 16

</div>

---

## What is this?

LLM agents are unreliable at choosing which API to call, because routing is usually left to a
prompt. NLPForge treats routing as a **retrieval problem that can be measured**. You describe
your APIs once as templates. For each request, it returns the one endpoint to call plus a
request body that passes the endpoint's schema. When a value is missing, it says which one,
instead of inventing it.

```text
"Refund 25 dollars on order 8820 because it arrived broken"
        │
        ▼
POST /orders/{order_id}/refund
{ "order_id": "8820", "amount": 25.0 }        extraction.ok = true · degraded = false
```

It is deliberately **not an agent**. There is no planning loop and no multi-step execution:
one request resolves to one endpoint.

## Key features

- **Semantic routing:** pgvector HNSW search over example utterances, max-pooled per template.
- **Structured extraction:** JSON-Schema-constrained decoding, Pydantic validation, one repair
  retry, and missing required fields reported explicitly.
- **Honest failure signalling:** every response carries per-stage outcomes and `degraded`, so
  "the request had no values" is distinguishable from "the LLM was unreachable".
- **Template catalogue:** documented APIs with a draft → review → approved workflow. Approval
  requires complete documentation, samples and schemas.
- **Dataset pipeline:** an LLM generates example utterances per template on Celery (your
  configured provider, Gemini, or the local Ollama model), or you upload a CSV. Both are
  embedded into pgvector and become routable.
- **Multi-tenant:** a tenant predicate on every vector query plus PostgreSQL row-level security,
  cookie-based JWT auth with refresh-token rotation, and a Redis-backed rate limiter.
- **Two runtimes:** fully offline on Ollama, or cloud mode with in-process ONNX embeddings.

## How it works

| Stage | What happens | Implementation |
|---|---|---|
| **1 · Recall** | Embed the request and retrieve the top-25 most similar utterances for the caller's tenant | `nomic-embed-text` → pgvector HNSW (cosine) |
| **2 · Rank** | Max-pool utterance scores per template; the best template is the route | `app/nlp/cross_encoder_reranker.py` (cross-encoder available, off by default) |
| **3 · Extract** | Fill the request body under the template's JSON Schema, validate, repair once | Ollama `llama3.2:3b` + Pydantic, behind a Redis circuit breaker |

```text
Next.js ──/api/*──► FastAPI ──► Stage 1 embed ─► pgvector (RLS + tenant filter)
                                 Stage 2 rank
                                 Stage 3 extract ─► Ollama ─► Pydantic ─► response
                    Celery ◄── dataset generation / embedding      Redis: queue · rate limits · JWT deny-list
```

Full request flow, data model, tenancy design and failure behaviour are in
**[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## Measured results

The benchmark has 180 held-out queries against 20 API templates, in four difficulty tiers.
Sibling endpoints such as password-reset-request, reset-confirm and change-password are
deliberately included as hard negatives. None of the queries appear in the indexed utterances.

| Strategy | Hit@1 | Hit@3 | Notes |
|---|---|---|---|
| **Dense retrieval + max-pool (shipped)** | **0.822** | 0.983 | `bge-small`, exact search; `python evals/run_eval.py --embedder onnx` (CI gate ≥ 0.78) |
| Same, through the live API (local mode) | 0.800 | 0.967 | `nomic-embed-text` via pgvector, full HTTP path |
| Dense + BM25 hybrid (RRF) | 0.806 | 0.956 | wins hard negatives (0.650), loses paraphrases |
| Dense + ms-marco cross-encoder | 0.739 | 0.944 | off-distribution for short commands, so disabled |
| v1 weighted heuristic | 0.589 | 0.850 | what the first version shipped |

The correct template is always in the top 25 (Recall@25 = 1.000), so all remaining error comes
from ranking. Routing takes about 100 ms p50 through the API without extraction. Extraction adds
about 1–5 s on CPU. Methodology and caveats are in **[evals/README.md](evals/README.md)**.

## Tech stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js 16 (App Router), React 18, TypeScript, Tailwind CSS (token-based design system), TanStack Query |
| Backend | FastAPI (async), SQLAlchemy 2, Pydantic v2, Alembic, Celery |
| AI / ML | Ollama (`nomic-embed-text`, `llama3.2:3b`), fastembed ONNX (`bge-small-en-v1.5`), FlashRank |
| Data | PostgreSQL 16 + pgvector (HNSW, row-level security), Redis |
| Infrastructure | Docker Compose, GitHub Actions (lint, tests, Postgres integration, benchmark gate, frontend build) |

## Project structure

```text
Backend/
  app/
    api/v1/            REST endpoints (query, templates, datasets, auth, settings)
    services/          routing pipeline, pgvector store, extraction, embedding
    nlp/               ranking, URL detection, BM25/RRF (benchmark arm)
    core/              config, tenancy (RLS), runtime (embedder), rate limiting
    demo_catalogue*.py the 20-template catalogue shared by the demo seed and the benchmark
  alembic/             migrations (pgvector, HNSW, RLS)
  scripts/             demo seed, migrations runner, Redis→pgvector backfill
  tests/               unit + Postgres integration tests
Frontend/              Next.js app (landing, dashboard, templates, datasets, settings)
evals/                 routing benchmark (180 held-out queries)
docs/                  architecture, demo GIF, screenshots
scripts/smoke_test.py  end-to-end check of a running stack
```

## Getting started

### Prerequisites

- Docker with Compose **v2.24+**
- About 6 GB of free RAM for the local LLM

### Run locally

```bash
git clone https://github.com/Iammilansoni/NLPFT-2.git
cd NLPFT-2
cp .env.example .env        # set POSTGRES_PASSWORD, REDIS_PASSWORD and SECRET_KEY
docker compose up -d --build
```

The first boot downloads about 2.3 GB of Ollama models. When `docker compose ps` shows the
backend as **healthy**, open **http://localhost:3000** and choose **Try the live demo**. The demo
tenant is seeded automatically with 20 complete, approved API templates.

Check the stack end to end:

```bash
pip install httpx && python scripts/smoke_test.py
```

### Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `POSTGRES_PASSWORD`, `REDIS_PASSWORD` | yes | service credentials |
| `SECRET_KEY` | yes | JWT signing key (≥ 32 characters) |
| `SECRET_KEY_ENCRYPTION` | recommended | Fernet key for stored LLM-provider API keys |
| `GEMINI_API_KEY` | optional | LLM dataset generation with a hosted model |
| `SMTP_*` | optional | verification and password-reset e-mails |
| `GOOGLE_CLIENT_ID` | optional | Google sign-in |

Every other setting has a working default; see [`.env.example`](.env.example). For running the
services without Docker, see [`docker-compose.dev.yml`](docker-compose.dev.yml) and
[`Backend/.env.example`](Backend/.env.example).

### Deployment

`Backend/Dockerfile.cloud` and `Backend/fly.toml` describe a Fly.io + Neon deployment with
in-process ONNX embeddings. That path is provided but has not been exercised end to end; see
[DEPLOYMENT.md](DEPLOYMENT.md).

## Usage

1. **Dashboard:** type a request such as *"change my password from oldpass1 to NewPass#9"*. You
   get the endpoint, the extracted body and the outcome of each stage.
2. **Templates:** add your own API with its method, endpoint, JSON Schema and samples, then
   submit it for review.
3. **Datasets:** generate example utterances for an approved template, or upload a CSV with a
   `query` column. Embedding makes them routable. Generation uses the provider set in
   **Settings → LLM Providers**; without one it falls back to `GEMINI_API_KEY`, then to the
   local Ollama model.
4. **API:** `POST /api/v1/query/semantic-search` with `{"query": "..."}`. OpenAPI docs are at
   http://localhost:8000/docs.

## Engineering decisions

- **Max-pool over mean.** A template with one exact utterance match should beat one with many
  lukewarm matches. v1's mean-based heuristic scored 23 points lower than plain dense retrieval.
- **The reranker ships off, and stays in the tree.** The cross-encoder lowered Hit@1 at every
  recall depth on this data. It remains a benchmark arm, so the decision can be re-checked when
  the embedder changes.
- **Constrained decoding plus validation.** The decoder cannot emit invalid JSON. Pydantic
  enforces types and required fields, and one repair retry feeds the error back. Blank or
  placeholder values count as missing, so the model cannot pad a required field.
- **Tenancy in two layers.** Superuser database roles bypass RLS, so every vector query also
  filters on the transaction-bound tenant. The health endpoint reports whether RLS is actually
  enforced for the connected role.
- **Transaction-scoped tenant binding.** `set_config(..., is_local => true)` instead of `SET`, so a
  pooled connection can never carry one tenant's identity into another request.

## Testing

| Suite | Scope | Runs in CI |
|---|---|---|
| `Backend/tests/unit` (152 tests) | routing orchestration, extraction and repair, circuit breaker, tenancy SQL, auth, demo catalogue completeness | yes |
| `Backend/tests/integration/test_rls_isolation.py` | migrations on an empty Postgres + cross-tenant isolation as a non-superuser role | yes |
| `evals/run_eval.py` | routing accuracy; merge gate at Hit@1 ≥ 0.78 | yes |
| `scripts/smoke_test.py` | full user loop against a running stack (login → route → create template → upload → embed → route → delete) | manual |
| Frontend | `tsc --noEmit`, ESLint, production build | yes |

## Limitations and next steps

- **Catalogue size.** 20 templates is small, and Hit@1 will fall as the catalogue grows. The
  dominant errors are sibling endpoints that differ by authentication state (hard-negative Hit@1
  is 0.625 live).
- **Reranking.** A cross-encoder fine-tuned on generated utterances is the obvious next
  experiment, and the harness is ready to measure it.
- **Cloud extraction.** Cloud mode has no hosted LLM wired into Stage 3 yet, so extraction
  reports `degraded` there.
- **Local generation is slow.** Dataset generation with the local 3B model on CPU takes minutes
  per batch, and its utterances are less varied than a hosted model's. Configure a hosted
  provider for real datasets.
- **RLS for CRUD.** The CRUD routers rely on explicit tenant filters. Running the API as a
  non-superuser role would enforce RLS for them too.

## Project history

| Version | What it is | Authorship |
|---|---|---|
| `v1.0-internship` | Internship prototype: FastAPI, Redis vectors, Celery, eight LLM providers | Team: Milan Soni, Avadhi Singhal, Abhilash Joshi |
| `v2` (this branch) | pgvector + RLS, measured routing, structured extraction, dual runtime, redesigned UI | Milan Soni |

## Author

**Milan Soni**, [github.com/Iammilansoni](https://github.com/Iammilansoni)

MIT licensed. See [LICENSE](LICENSE).
