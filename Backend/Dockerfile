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

# Copy additional files
COPY --chown=appuser:appuser *.py ./
COPY --chown=appuser:appuser *.json ./ 

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application with uvicorn
# Use exec so uvicorn replaces the shell and receives signals (SIGTERM, etc.) directly
CMD exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-1}
