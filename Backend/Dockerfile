# NLPForge backend — LOCAL mode image (embeddings + extraction via Ollama).
# Also used by the Celery worker service. Cloud mode: see Dockerfile.cloud.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_DEFAULT_TIMEOUT=300 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Only used if RERANKER_ENABLED=true; must be writable by appuser.
    RERANKER_CACHE_DIR=/app/.cache/flashrank

RUN useradd -m -u 1000 appuser

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/datasets /app/.cache/fastembed && chown -R appuser:appuser /app
USER appuser

COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser scripts/ ./scripts/
# Boot scripts: init_db_direct.py, seed_admin.py
COPY --chown=appuser:appuser *.py ./

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Boot sequence -- every step is idempotent, so this runs on every start:
#   init_db_direct.py    create_all() for every ORM-mapped table
#   run_migrations.py    stamp the create_all() baseline once, then
#                        `alembic upgrade head` for what exists only as a
#                        migration (vector_rows, HNSW indexes, RLS policies)
#   seed_admin.py        admin account, only when the users table is empty
#   seed_demo.py         demo tenant (20 templates, embedded) when SEED_DEMO=true;
#                        a seed failure is logged and does not stop the API
# The demo seed needs evals/api_surface.py, which docker-compose bind-mounts.
CMD python init_db_direct.py \
 && python scripts/run_migrations.py \
 && python seed_admin.py \
 && { [ "$SEED_DEMO" != "true" ] || python scripts/seed_demo.py || echo "demo seed failed; starting API anyway"; } \
 && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-1}
