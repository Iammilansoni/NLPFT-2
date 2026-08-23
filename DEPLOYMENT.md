# Deploying NLPForge

Two supported shapes, selected by `EXECUTION_MODE`.

| | **Local** | **Cloud** |
|---|---|---|
| Embeddings | Ollama `nomic-embed-text` (768-dim) | in-process ONNX `bge-small-en-v1.5` (384-dim) |
| Generation | Ollama | hosted API (Gemini Flash / Groq / OpenRouter) |
| Reranking | FlashRank `ms-marco-MiniLM-L-12-v2` | same |
| Vectors | PostgreSQL + pgvector | same |
| Services | 6 containers | 1 container + managed Postgres |
| RAM floor | ~8 GB | ~512 MB |
| Cost | £0, offline | ~$0–15/mo + token usage |
| API keys | none | one |

---

## Why cloud mode exists

Ollama is the single reason v1 could not be deployed. It wants 4–8 GB of RAM and
realistically a GPU. No free tier hosts it, and a VM that runs it costs more than
every other component combined. Every "I'll deploy it later" plan for this
project died there.

Cloud mode runs a 130 MB ONNX embedder *inside* the FastAPI process. No model
server, no GPU. The stack collapses to **FastAPI + PostgreSQL**, which fits
anywhere.

Local mode is not a downgrade — it is the zero-key, fully-offline story, and
worth keeping for exactly that.

> **Switching modes requires a re-embed.** Local is 768-dim, cloud is 384-dim.
> `vector_rows` stores model and dimension per row and Stage 1 filters on both, so
> a mismatch produces an explicit compatibility error rather than silently
> meaningless distances.

---

## Local mode

```bash
cp Backend/.env.example Backend/.env     # set POSTGRES_PASSWORD, REDIS_PASSWORD
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed_demo.py
```

`http://localhost:3000` — log in as `demo@nlpforge.dev` / `DemoForge!2026` and
query *"I forgot my password, send me a reset link"*.

---

## Cloud mode

### 1. Database — Neon (free tier)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

> **asyncpg + pooled Postgres.** Neon and Supabase front Postgres with pgbouncer.
> asyncpg's prepared-statement cache breaks against transaction pooling with
> `DuplicatePreparedStatementError` under concurrency — intermittently, so it
> passes a smoke test and fails in production. Use the **direct** (non-pooled)
> connection string, or append `?prepared_statement_cache_size=0`.

pgvector 0.8+ is required for `hnsw.iterative_scan`. Without it, RLS post-filters
HNSW results and a small tenant silently gets zero rows. Verify:

```sql
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

### 2. Backend — Fly.io

```bash
fly launch --dockerfile Backend/Dockerfile.cloud --no-deploy

fly secrets set \
  DATABASE_URL="postgresql+asyncpg://...?prepared_statement_cache_size=0" \
  GEMINI_API_KEY="..." \
  SECRET_KEY="$(openssl rand -hex 32)" \
  SECRET_KEY_ENCRYPTION="$(openssl rand -base64 32)" \
  EXECUTION_MODE=cloud \
  VECTOR_BACKEND=pgvector

fly deploy
fly ssh console -C "python scripts/seed_demo.py"
```

Size for **1 GB RAM**. The floor is roughly 130 MB embedder + 34 MB reranker +
~200 MB Python/onnxruntime; 512 MB works but leaves no headroom for two uvicorn
workers.

Both ONNX models are baked into the image at build time. A cold start that must
fetch 160 MB of weights before serving is not a cold start, it is an outage.

### 3. Frontend — Vercel

```bash
cd Frontend && vercel --prod   # NEXT_PUBLIC_API_URL = your Fly URL
```

### 4. Redis — optional

Cloud mode no longer needs Redis for vectors. It is still used for rate
limiting, the JWT denylist, the semantic cache, and Celery. Upstash's free tier
covers all four. Without it: rate limiting falls back to in-memory, the circuit
breaker degrades to per-process, and background generation is unavailable.

> Redis Cloud free tier does **not** include RediSearch on all plans. That only
> matters if you set `VECTOR_BACKEND=redis`; the default pgvector path is
> unaffected.

---

## Cost

| | Free tier | Realistic |
|---|---|---|
| Neon Postgres | 0.5 GB | $0 |
| Fly.io backend | ~3 shared VMs | $0–7 |
| Vercel frontend | hobby | $0 |
| Upstash Redis | 10k cmd/day | $0 |
| Gemini Flash | generous | $0–5 |
| **Total** | | **$0–12/mo** |

---

## Migrating existing data

Phase 3 creates an empty `vector_rows`. Without a backfill, everything users
already embedded stops being findable — with no error explaining why.

```bash
python scripts/backfill_redis_to_pgvector.py --dry-run   # validate first
python scripts/backfill_redis_to_pgvector.py
python evals/run_eval.py                                  # confirm quality held
```

Read-only against Redis. Nothing is deleted; if the result is wrong, set
`VECTOR_BACKEND=redis` and try again. Keep the Redis data until you have verified
retrieval.

---

## Post-deploy verification

```bash
curl https://<app>/api/v1/health          # execution_mode, embedder, dimension
```

Then confirm RLS is not merely enabled but **forced** — `ENABLE ROW LEVEL
SECURITY` is silently ignored for the table owner, and applications routinely
connect as the owner:

```sql
SELECT relname, relrowsecurity, relforcerowsecurity
FROM pg_class WHERE relname IN ('templates','datasets','vector_rows');
```

All three must be `t, t`. If `relforcerowsecurity` is `f`, **tenant isolation is
not in effect** despite the migration having succeeded. The app also asserts this
at startup via `verify_rls_enforced()`.

---

## Operational notes

**Right-size `STAGE1_TOP_K` after any embedder change.** Measured on the current
benchmark, k=25 beats k=50 on Hit@1 *and* halves latency — more marginal
candidates give the cross-encoder more chances to be confidently wrong. Re-run
`evals/run_eval.py` and re-tune; do not assume deeper is better.

**Reranking dominates latency** (~265 ms p50 of a ~300 ms request). The Stage 0
semantic cache is the highest-leverage optimisation, not a faster reranker —
`ms-marco-TinyBERT-L-2-v2` is 6× faster and surrenders the entire hard-negative
accuracy gain.

**Set `OMP_NUM_THREADS=1`** (already in `Dockerfile.cloud`). ONNX and FlashRank
parallelise internally; letting each spawn a pool per uvicorn worker
oversubscribes small cloud CPUs and makes p95 worse.

**Celery is optional in cloud mode.** Without a worker, dataset generation is
unavailable but routing, extraction, and the demo all work. Add one when you need
generation.
