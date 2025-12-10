#app/core/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    app_name = "NLPForge API"
    app_version = "0.1.0"
    description = "AI-powered NLP testing framework with semantic search and dataset generation"
    host = "127.0.0.1"
    port = 8000
    workers = 1
    debug = True
    log_level = "info"
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Security settings - MUST be set in environment variables
    secret_key: str = os.getenv("SECRET_KEY", "")
    
    # Email settings
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "noreply@nlpforge.com")
    smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "NLPForge")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # PostgreSQL Configuration (Main Brain - Permanent Storage)
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user = os.getenv("POSTGRES_USER", "nlpforge")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "nlpforge_password")
    postgres_db = os.getenv("POSTGRES_DB", "nlpforge")
    database_url = os.getenv(
        "DATABASE_URL",
        f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    )
    
    # Datasets directory
    @property
    def project_root(self) -> Path:
        """Get the Backend directory as project root."""
        # Navigate from app/core/config.py to Backend/
        current_file = Path(__file__).resolve()  # app/core/config.py
        app_dir = current_file.parent.parent      # app/
        backend_dir = app_dir.parent              # Backend/
        return backend_dir
    
    @property
    def datasets_path(self) -> Path:
        """Get the datasets directory path: Backend/datasets"""
        return self.project_root / "datasets"

settings = Settings()

# Validate SECRET_KEY on startup
if not settings.secret_key or len(settings.secret_key) < 32:
    if settings.environment == "development":
        # Allow weak key in development but warn loudly
        import warnings
        warnings.warn(
            "\n" + "="*80 + "\n"
            "⚠️  WARNING: SECRET_KEY is missing or too short!\n"
            "   This is ONLY allowed in development mode.\n"
            "   Generate a secure key with:\n"
            "   python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
            "   Then add to .env file: SECRET_KEY=<generated_key>\n"
            + "="*80,
            UserWarning,
            stacklevel=2
        )
        # Use a weak development key (DO NOT use in production)
        settings.secret_key = "dev-insecure-key-DO-NOT-USE-IN-PRODUCTION-" + "x" * 10
    else:
        # In production/staging, this is a critical error
        raise ValueError(
            "❌ CRITICAL: SECRET_KEY must be set in environment variables and be at least 32 characters long.\n"
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
            "Then add to .env file: SECRET_KEY=<generated_key>"
        )

# Ensure datasets directory exists
DATASETS_DIR = settings.datasets_path
DATASETS_DIR.mkdir(exist_ok=True, parents=True)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "nlpforge_redis_secure_password_2024")
MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-small-en-v1.5")
INDEX_NAME = os.getenv("INDEX_NAME", "idx:api")
TOP_K = int(os.getenv("TOP_K", "5"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))


# Ollama Configuration (LOCAL LLM for dataset generation)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b-instruct-q4_K_M")  # Primary: Gemma 2B Instruct (faster, lighter)
OLLAMA_FALLBACK_MODEL = os.getenv("OLLAMA_FALLBACK_MODEL", "llama3.2:3b-instruct-q4_K_M")  # Fallback: Llama 3.2 Instruct (quantized)

# Intent detection method: "vector_search" or "pattern_matching"
INTENT_DETECTION_METHOD = os.getenv("INTENT_DETECTION_METHOD", "vector_search")

# Security settings - Use settings.secret_key (validated on startup)
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Email settings (for password reset and verification)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@nlpforge.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "NLPForge")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
