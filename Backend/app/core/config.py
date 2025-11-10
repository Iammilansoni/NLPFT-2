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

# Ensure datasets directory exists
DATASETS_DIR = settings.datasets_path
DATASETS_DIR.mkdir(exist_ok=True, parents=True)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
MODEL_NAME = os.getenv("MODEL_NAME", "BAAI/bge-small-en-v1.5")
INDEX_NAME = os.getenv("INDEX_NAME", "idx:apis")
TOP_K = int(os.getenv("TOP_K", "5"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))


# Gemini API key for dataset generation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")