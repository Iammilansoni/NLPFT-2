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
COPY requirements-docker.txt ./requirements.txt

# Install PyTorch CPU-only version first to avoid large CUDA dependencies
RUN pip install --no-cache-dir --default-timeout=300 \
    torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install remaining requirements
RUN pip install --no-cache-dir --default-timeout=300 -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt wordnet averaged_perceptron_tagger

# Copy application code
COPY app/ ./app/

# Copy additional files
COPY *.py ./
COPY *.json ./ 

# Create necessary directories
RUN mkdir -p /app/storage /app/datasets /app/storage/faiss_index

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
