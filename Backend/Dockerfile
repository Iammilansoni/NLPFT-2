# Multi-stage build for NLPForge Backend API
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set pip configuration for better reliability
ENV PIP_DEFAULT_TIMEOUT=300 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy requirements and install Python dependencies
COPY requirements.txt ./requirements.txt

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Install requirements (no PyTorch needed - using Ollama HTTP API)
RUN pip install --no-cache-dir --default-timeout=300 -r requirements.txt

# Create necessary directories and set permissions
RUN mkdir -p /app/storage /app/datasets /app/storage/faiss_index /app/storage/flashrank_cache && \
    chown -R appuser:appuser /app

# Switch to appuser
USER appuser

# Copy application code
COPY --chown=appuser:appuser app/ ./app/

# Copy database migration files
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic/ ./alembic/

# Operational scripts. seed_demo.py is the documented one-click demo path
# (`docker compose exec backend python scripts/seed_demo.py`), so it has to be
# present in the local image too — Dockerfile.cloud already copies this.
COPY --chown=appuser:appuser scripts/ ./scripts/

# Copy additional files
COPY --chown=appuser:appuser *.py ./
COPY --chown=appuser:appuser *.json ./ 

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run DB init, seed admin user, then start the application
# init_db_direct.py creates all tables from SQLAlchemy models (idempotent - safe to run every time)
# seed_admin.py creates a default admin user if the users table is empty (idempotent)
CMD python init_db_direct.py && python seed_admin.py && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-1}
