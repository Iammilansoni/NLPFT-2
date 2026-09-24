# Architecture

NLPForge resolves **one natural-language request to one API endpoint** and returns a request
body that validates against that endpoint's JSON Schema. This document covers how a request
flows through the system, where state lives, and why the main design decisions were made.

## System overview

```
Browser ──► Next.js 16 (App Router)
              │  same-origin /api/*  (rewrite proxy → backend:8000, HttpOnly JWT cookies)
              ▼
           FastAPI ── auth · rate limiting (Redis) · structured errors · request tracing
              │
              ├── Routing pipeline      app/services/multi_model_semantic_service.py
              │     Stage 1  embed + recall     app/services/model_access.py, app/services/pgvector_store.py
              │     Stage 2  rank templates     app/nlp/cross_encoder_reranker.py
              │     Stage 3  extract body       app/services/structured_extraction_service.py
              │
              ├── Template catalogue    app/api/v1/template_builder.py  (draft → review → approved)
              ├── Datasets              app/api/v1/datasets.py → Celery worker → LLM generation
              ├── Embedding             app/services/multi_model_embedding_service.py → Celery worker → pgvector
              └── Providers & models    app/llm/provider_registry.py, model_discovery.py, embeddings.py

PostgreSQL 16 + pgvector   users, templates, datasets, vector_rows (HNSW), model catalogue, RLS policies
Redis                      Celery broker/results, rate-limit counters, JWT deny-list, breaker state
Ollama (local mode)        default embeddings (nomic-embed-text) and llama3.2:3b extraction
Hosted providers           any of ~20 in the registry, with the user's own key or a deployment key
```

## Request flow: `POST /api/v1/query/semantic-search`

| Step | What happens | Code |
|---|---|---|
| 1. Embed | The query is embedded with the caller's embedding model: their choice in Settings → Embedding model, else the deployment default (Ollama `nomic-embed-text` locally, in-process ONNX `bge-small-en-v1.5` in cloud mode). | `services/model_access.py` |
| 2. Recall | KNN over `vector_rows` inside a transaction bound to the caller's tenant: `u_id = current_setting('app.tenant_id')`, plus `embedding_provider`, `embedding_model` and `dimension` filters, HNSW cosine, top-25. | `services/pgvector_store.py` |
| 3. Rank | Row scores are max-pooled per template. The top template is the route. A FlashRank cross-encoder is implemented but off by default (see "Decisions" below). | `nlp/cross_encoder_reranker.py` |
| 4. Resolve | The winning template (endpoint, method, request schema) is loaded from Postgres. | `multi_model_semantic_service.py` |
| 5. Extract | **Rules** first read values the request states outright, using only the schema: email formats, identifiers after their noun ("order 8820"), secrets after their name, enum words, numbers. Then an **LLM**, only for fields still empty and only if the request has unexplained words: the user's own chat connection, else local Ollama under schema-constrained decoding. Then **grounding**: each model value must appear in the request, or it goes to `unverified` instead of the body. Every field reports its `source` and `confidence`. | `services/extraction_rules.py`, `services/structured_extraction_service.py` |
| 6. Respond | Returns the route, the extracted body, per-stage outcomes and timings. `degraded: true` only when an enabled stage could not run. | `api/v1/multi_model_query.py` |

## Where data lives

| Data | Store | Notes |
|---|---|---|
| Templates, parameters, samples, status | Postgres | Status is kept in the `metadata` table (draft/review/approved). |
| Generated / uploaded datasets | Postgres `datasets`, `csv_data` + CSV on a shared volume | Written by the Celery worker. |
| Routable vectors | Postgres `vector_rows` | One row per utterance, storing `embedding_provider`, `embedding_model` and `dimension`. A partial HNSW index per dimension is created the first time a model of that width is used: `vector` up to 2000 dims, `halfvec` up to 4000, exact search beyond. |
| Embedding choice | Postgres `user_settings` | (provider, model, measured dimension); empty means the deployment default. |
| Sessions | HttpOnly cookies (JWT) + Redis deny-list | Access tokens are short-lived; refresh tokens rotate. |
| Model catalogue | Postgres `model_catalog`, `model_catalog_sources` | Every model each provider reports serving, with its lifecycle state and the health of each provider's last sync. |

## Model catalogue

No model list is written into the code. `app/llm/model_discovery.py` asks each
provider what it serves right now (Ollama `/api/tags` + `/api/show`, Gemini
`models.list`, Anthropic `/v1/models`, the built-in ONNX library's own model list, and
the OpenAI-style `/models` of every other provider in `app/llm/provider_registry.py`). Whether a model is for chat or embeddings comes from
the provider's own metadata where it exists. An embedding model's dimension is read
from provider metadata, or measured by embedding one string. It is never guessed from
the name.

A Celery Beat job (`MODEL_CATALOG_SYNC_MINUTES`, default 6 h) and every change to a
user's connection re-sync the catalogue (`app/services/model_catalog_service.py`):

| Event | Result |
|---|---|
| A provider lists a model for the first time | Added. After the provider's first sync, new arrivals get a "New" badge. |
| A successful listing no longer includes a model | `deprecated`: still usable, and flagged on every connection that uses it |
| Still missing after `MODEL_RETIRE_GRACE_HOURS` (72), or past a shutdown date the provider announced | `retired`: hidden from pickers |
| Retired, unused, and older than `MODEL_RETIRED_RETENTION_DAYS` (7) | Deleted. A model still referenced by a connection or dataset is never deleted. |
| A provider is unreachable, or one of its keys fails | No lifecycle change. An outage must not retire a provider's models. |

Models found with deployment or public credentials are shared. Models found with a
user's own key are visible only to that user, so private models (fine-tunes, custom
endpoints) never leak between tenants. Only Ollama and custom endpoints accept a
user-supplied URL, and link-local addresses such as cloud metadata services are refused.

## Embedding models

Each user picks an embedding model from any provider in
`app/llm/provider_registry.py` that offers embeddings: local (Ollama, built-in ONNX,
a custom server) or hosted (Gemini, OpenAI, Mistral, Cohere, NVIDIA, Jina, Together,
OpenRouter, ...). A hosted provider is listed whether or not the deployment has a key
for it: the user's own saved key is used first, then a deployment-wide key.

Vectors from different models cannot be compared, so the triple
**(provider, model, dimension)** is recorded on every dataset and vector row, and search
filters on all three. Choosing a model makes one real embedding call, which verifies the
key and model and measures the dimension instead of trusting a number.

When data and search use different models, nothing is compared silently:

| Situation | What the user sees |
|---|---|
| Searching a dataset embedded with another model | `MODEL_MISMATCH` with two options: switch to that model, or re-embed the dataset |
| Nothing indexed for the active model, but other models have data | `MODEL_MISMATCH` listing those datasets, with *switch* and *re-embed all* |
| Results found, but some datasets use other models | Results, plus `metadata.excluded_datasets` and the same options |
| The provider needs a key the user doesn't have | `EMBEDDING_FAILED`, and the message says where to add one |

Embedding runs on the Celery worker, so a free-tier provider's rate limits cannot time out
a request. The client honours `Retry-After` and backs off. If a provider keeps refusing,
the dataset records a plain-English reason.

## Tenancy

Tenant isolation is enforced in two independent layers:

1. **Query layer.** Every vector read and delete runs inside `tenant_session(user_id)`, which
   binds `app.tenant_id` with `set_config(..., is_local => true)`. Because the binding is
   transaction-scoped, it cannot leak to the next request that reuses the pooled connection.
   The SQL filters on that bound value explicitly.
2. **Database layer.** Row-level security policies on `templates`, `datasets`, `csv_data`,
   `embeddings` and `vector_rows` are ENABLED and FORCED.

PostgreSQL skips RLS entirely for superuser and `BYPASSRLS` roles, and the official Postgres
image makes `POSTGRES_USER` a superuser. That is why layer 1 exists. At startup the API
reports whether layer 2 is actually in effect (`/api/v1/health` → `runtime.rls_enforced`).
CI runs the isolation tests as a non-superuser role, where both layers apply.

To enforce RLS in the database for the whole application, connect the API with a
non-superuser role. The CRUD routers still use explicit `u_id` filters, so they keep working
under either role.

## Decisions, and the measurements behind them

All numbers come from `python evals/run_eval.py --embedder onnx`: 180 held-out queries against
the 20-template demo catalogue, reproduced in CI on every push.

| Decision | Evidence |
|---|---|
| Max-pool rows into a template score instead of the mean | One exact utterance match should beat many near-misses. v1's mean-based heuristic scored Hit@1 0.589, versus 0.822 for dense max-pool. |
| Ship the cross-encoder **off** | `ms-marco-MiniLM` lowered Hit@1 from 0.822 to 0.739 at every recall depth. It was trained on web-search prose, while this corpus is short imperative requests. |
| BM25 hybrid available but not the default | It wins the hard-negative tier (0.600 → 0.650) but loses overall (0.806). That difference is within noise at n=180, so it did not earn default status. |
| Recall depth k = 25 | Recall@25 is 1.000 on this catalogue, so all remaining error is in ranking. |
| pgvector instead of Redis vectors | A single store keeps vectors transactionally consistent with templates, and tenancy can be enforced by Postgres. |
| Constrained decoding + Pydantic + repair | Malformed JSON becomes unrepresentable. Validation errors are fed back once, and a failure is reported instead of returning `{}`. |

Live measurement through the API in local mode (`nomic-embed-text` through pgvector, re-measured
after per-user embedding models landed): Hit@1
0.800 and Hit@3 0.967 over the same 180 queries.

## Failure behaviour

| Failure | Result |
|---|---|
| Embedder unreachable | `success: false, error: EMBEDDING_FAILED` |
| No indexed utterances | `success: false, error: NO_RESULTS` with guidance to embed a dataset |
| Dataset embedded with another model | `MODEL_MISMATCH` with options to switch model or re-embed; vectors are never compared across models |
| Provider rate-limits embedding | Retried with backoff on the worker; a persistent limit is recorded on the dataset in plain words |
| LLM unreachable / circuit open | Route still returned. Rule-extracted values are kept; `degraded=true`, with the reason. The user's model falls back to the local one first |
| Model proposes a value the request doesn't contain | Not used: listed in `extraction.unverified` with the reason (e.g. "the model copied the whole request") |
| Required field absent from the request | `extraction.ok=false`, partial `values`, `missing_required: [...]` |

## Known limitations

- The benchmark catalogue has 20 templates. Hit@1 will fall as the catalogue grows, and
  sibling endpoints that differ only by authentication state are the dominant error class.
- Extraction runs a 3B model on CPU. It takes about 1–5 s warm, and the first call after a
  cold start is slower.
- Cloud mode (ONNX embeddings) has no hosted extraction provider wired in, so extraction
  reports `degraded` there.
- The Fly.io / Neon deployment configuration is provided but has not been exercised end to end.
