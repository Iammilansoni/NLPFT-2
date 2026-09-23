# Deploying NLPForge

There are two runtime shapes, selected by `EXECUTION_MODE`.

| | **Local** (`docker compose`) | **Cloud** (`Backend/Dockerfile.cloud`) |
|---|---|---|
| Embeddings | Ollama `nomic-embed-text` (768-d) | in-process ONNX `bge-small-en-v1.5` (384-d) |
| Extraction | Ollama `llama3.2:3b` | not wired to a hosted LLM; responses report `degraded` |
| Vectors | PostgreSQL + pgvector | PostgreSQL + pgvector |
| Services | 7 containers | 1 container + managed Postgres (Redis optional) |
| Status | **verified**: boots from a clean clone | configured, **not exercised end to end** |

Switching modes requires re-embedding, because vectors are only comparable within one
(model, dimension) pair. Every vector row records both values, so a mismatch surfaces as an
explicit `MODEL_MISMATCH` error instead of meaningless distances.

---

## Local (Docker Compose)

Requires Docker with Compose v2.24 or later.

```bash
cp .env.example .env          # set POSTGRES_PASSWORD, REDIS_PASSWORD, SECRET_KEY
docker compose up -d --build
```

The first boot downloads about 2.3 GB of Ollama models through the `ollama-pull` one-shot
service. Later boots skip the download.

The backend container's boot sequence is idempotent and runs on every start:

1. `init_db_direct.py` creates every ORM table.
2. `scripts/run_migrations.py` stamps that baseline once, then runs `alembic upgrade head`
   (pgvector, HNSW indexes, RLS policies).
3. `seed_admin.py` creates an admin account, only when there are no users.
4. `scripts/seed_demo.py` runs when `SEED_DEMO=true` (the default). It creates the demo tenant:
   20 complete, approved templates and 100 embedded utterances.

The stack is ready when `docker compose ps` shows `backend` as healthy. Open
http://localhost:3000 and choose **Try the demo**, or sign in as
`demo@nlpforge.dev` / `DemoForge!2026`.

| Port | Service |
|---|---|
| 3000 | frontend (`FRONTEND_PORT`) |
| 8000 | API, `/docs` for OpenAPI (`BACKEND_PORT`) |
| 127.0.0.1:5433 | Postgres (`POSTGRES_PORT_HOST`) |
| 127.0.0.1:6379 | Redis (`REDIS_PORT_HOST`) |

### Tenancy note

The official Postgres image makes `POSTGRES_USER` a superuser, and superusers bypass
row-level security. The vector queries stay tenant-scoped through their explicit tenant
predicate. `/api/v1/health` reports `runtime.rls_enforced: false` so the configuration is
visible. To enforce RLS in the database as well, create a non-superuser role, grant it the
tables, and point `DATABASE_URL` at it. CI runs the isolation tests exactly that way.

---

## Cloud (Fly.io + Neon) — provided, unverified

Run these from `Backend/`, so the build context matches `Dockerfile.cloud`:

```bash
cd Backend
fly launch --no-deploy --copy-config
fly secrets set \
  DATABASE_URL="postgresql+asyncpg://USER:PASS@HOST/DB?prepared_statement_cache_size=0" \
  SECRET_KEY="$(openssl rand -hex 32)" \
  SECRET_KEY_ENCRYPTION="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  SEED_DEMO=true
fly deploy
```

- The Neon role needs the `vector` extension (`CREATE EXTENSION vector;`), pgvector 0.8+ for
  `hnsw.iterative_scan`, and `CREATEROLE` if you want the `nlpforge_admin` maintenance policy.
  Without `CREATEROLE`, the migration skips that policy instead of failing.
- asyncpg with pooled Postgres needs `prepared_statement_cache_size=0` (pgbouncer transaction
  pooling).
- Redis (Upstash) is optional. Without it, rate limiting falls back to in-process memory and
  dataset generation is unavailable.
- Frontend on Vercel: set `BACKEND_INTERNAL_URL` to the Fly URL **at build time**, so the
  browser keeps calling same-origin `/api/*`. That keeps cookies first-party.

---

## Post-deploy checks

```bash
curl https://<host>/api/v1/health     # status, execution_mode, embedder, rls_enforced
```

Then sign in and route a request from the dashboard. `extraction.ok: true` confirms that
Stage 3 reached the LLM.
