#app/core/config.py

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from Backend directory (where this config file resides)
_backend_dir = Path(__file__).resolve().parent.parent.parent  # app/core/config.py -> Backend/
_env_file = _backend_dir / ".env"
load_dotenv(_env_file)


def _require_env(key: str, description: str = None) -> str:
    """Get required environment variable or raise error."""
    value = os.getenv(key)
    if not value:
        desc = f" ({description})" if description else ""
        raise ValueError(
            f"❌ REQUIRED: {key} must be set in environment variables{desc}.\n"
            f"Add to Backend/.env: {key}=<your_value>"
        )
    return value


class Settings:
    app_name = "NLPForge API"
    app_version = "0.1.0"
    description = "AI-powered NLP testing framework with semantic search and dataset generation"
    host = "127.0.0.1"
    port = 8000
    workers = 1
    debug = os.getenv("DEBUG", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Security settings - MUST be set in environment variables
    secret_key: str = os.getenv("SECRET_KEY", "")
    
    # Email/SMTP settings - read from env
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "")
    smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "NLPForge")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # PostgreSQL Configuration - read from env
    postgres_host = os.getenv("POSTGRES_HOST", "")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user = os.getenv("POSTGRES_USER", "")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")
    postgres_db = os.getenv("POSTGRES_DB", "")
    database_url = os.getenv("DATABASE_URL", "")
    
    # Datasets directory
    @property
    def project_root(self) -> Path:
        """Get the Backend directory as project root."""
        current_file = Path(__file__).resolve()
        app_dir = current_file.parent.parent
        backend_dir = app_dir.parent
        return backend_dir
    
    @property
    def datasets_path(self) -> Path:
        """Get the datasets directory path: Backend/datasets"""
        return self.project_root / "datasets"

settings = Settings()

# Validate SECRET_KEY on startup
if not settings.secret_key or len(settings.secret_key) < 32:
    if settings.environment == "development":
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
        settings.secret_key = "dev-insecure-key-DO-NOT-USE-IN-PRODUCTION-" + "x" * 10
    else:
        raise ValueError(
            "❌ CRITICAL: SECRET_KEY must be set in environment variables and be at least 32 characters long.\n"
            "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
            "Then add to .env file: SECRET_KEY=<generated_key>"
        )

# Validate DATABASE_URL
if not settings.database_url and not (settings.postgres_host and settings.postgres_user and settings.postgres_password):
    if settings.environment != "development":
        raise ValueError(
            "❌ CRITICAL: Database configuration required.\n"
            "Set DATABASE_URL or (POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB) in .env"
        )

# Build database URL from components if not directly provided
if not settings.database_url and settings.postgres_host:
    settings.database_url = (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )

# =============================================================================
# SMTP VALIDATION - REQUIRED for email functionality (skip in testing)
# =============================================================================
_testing = os.getenv("TESTING", "").lower() in ("1", "true", "yes")
if not settings.smtp_user or not settings.smtp_password:
    if settings.environment in ("development", "testing") or _testing:
        import warnings
        warnings.warn(
            "\n" + "="*80 + "\n"
            "⚠️  WARNING: SMTP_USER / SMTP_PASSWORD not set.\n"
            "   Email features (registration, password reset) will NOT work.\n"
            "   Add SMTP_USER and SMTP_PASSWORD to Backend/.env\n"
            + "="*80,
            UserWarning,
            stacklevel=2,
        )
        settings.smtp_user = settings.smtp_user or "noreply@localhost"
        settings.smtp_password = settings.smtp_password or "placeholder"
    else:
        raise ValueError(
            "❌ CRITICAL: SMTP configuration is required.\n"
            "Email functionality (registration, password reset) requires:\n"
            "  SMTP_USER=your_email@gmail.com\n"
            "  SMTP_PASSWORD=your_app_password\n\n"
            "For Gmail, create an App Password at:\n"
            "  Google Account → Security → 2-Step Verification → App Passwords\n\n"
            "Add these to Backend/.env"
        )

# Ensure datasets directory exists
DATASETS_DIR = settings.datasets_path
DATASETS_DIR.mkdir(exist_ok=True, parents=True)

# =============================================================================
# REDIS CONFIGURATION - All values from environment
# =============================================================================
REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Validate Redis in non-development
if not REDIS_HOST and settings.environment != "development":
    raise ValueError("❌ CRITICAL: REDIS_HOST must be set in environment variables.")
elif not REDIS_HOST:
    REDIS_HOST = "localhost"  # Development fallback only

# =============================================================================
# OLLAMA CONFIGURATION - All values from environment
# =============================================================================
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "")
MODEL_NAME = os.getenv("OLLAMA_EMBEDDING_MODEL", os.getenv("MODEL_NAME", ""))

# Validate Ollama in non-development
if not OLLAMA_HOST and settings.environment != "development":
    raise ValueError("❌ CRITICAL: OLLAMA_HOST must be set in environment variables.")
elif not OLLAMA_HOST:
    OLLAMA_HOST = "http://localhost:11434"  # Development fallback only

if not MODEL_NAME:
    MODEL_NAME = "nomic-embed-text"  # Safe default for embedding model

# =============================================================================
# GEMINI API - Required for dataset generation
# =============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Note: Validation happens in dataset_generator.py when actually used

# =============================================================================
# JWT/SECURITY SETTINGS
# =============================================================================
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))  # 24 hours default
