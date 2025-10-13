# Dockerfile for NLPForge Backend API
# Using Python 3.11 (trying alternative base if pull fails)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set pip configuration for better reliability
ENV PIP_DEFAULT_TIMEOUT=300 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Install PyTorch CPU-only version first to avoid large CUDA dependencies
RUN pip install --no-cache-dir --default-timeout=300 \
    torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining requirements with increased timeout
RUN pip install --no-cache-dir --default-timeout=300 -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt wordnet averaged_perceptron_tagger

# Copy application code
COPY app/ ./app/

# Copy dataset generator module (needed for API dataset generation)
COPY generate_api_dataset.py ./

# Create necessary directories
RUN mkdir -p /app/storage /app/datasets

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
