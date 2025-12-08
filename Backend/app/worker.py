"""
Celery Worker Configuration
===========================
Handles asynchronous tasks for NLPForge:
- Dataset generation
- Embedding computations
- Email notifications
- Background data processing
"""

import os
import logging
from celery import Celery
from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis configuration from settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Construct Redis URLs with authentication
if REDIS_PASSWORD:
    redis_base = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
else:
    redis_base = f"redis://{REDIS_HOST}:{REDIS_PORT}"

# Celery uses Redis DB 1 for broker, DB 2 for results
BROKER_URL = f"{redis_base}/1"
BACKEND_URL = f"{redis_base}/2"

# Initialize Celery application
celery_app = Celery(
    "nlpforge_worker",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=[
        "app.services.dataset_service",
        "app.services.embedding_service",
        "app.services.email_service",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    result_expires=86400,  # Results expire after 24 hours
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker crashes
    broker_connection_retry_on_startup=True,  # Retry Redis connection on startup
)

# Task routing configuration
celery_app.conf.task_routes = {
    "app.services.dataset_service.generate_dataset_async": {"queue": "dataset_generation"},
    "app.services.embedding_service.create_embedding_async": {"queue": "embeddings"},
    "app.services.embedding_service.reembed_dataset_async": {"queue": "embeddings"},
    "app.services.email_service.send_email_async": {"queue": "notifications"},
}

# Import tasks to register them
# Note: Tasks must be imported for Celery to discover them, but we handle import errors gracefully
try:
    # Import tasks individually to identify which ones are failing
    try:
        from app.services.dataset_service import generate_dataset_async
        logger.info("✅ Registered task: generate_dataset_async")
    except Exception as e:
        logger.warning(f"⚠️ Could not register dataset_service tasks: {e}")
    
    try:
        from app.services.email_service import send_email_async
        logger.info("✅ Registered task: send_email_async")
    except Exception as e:
        logger.warning(f"⚠️ Could not register email_service tasks: {e}")
    
    try:
        from app.services.embedding_service import create_embedding_async, reembed_dataset_async
        logger.info("✅ Registered task: create_embedding_async")
        logger.info("✅ Registered task: reembed_dataset_async")
    except Exception as e:
        logger.warning(f"⚠️ Could not register embedding_service tasks: {e}")
    
except Exception as e:
    logger.error(f"❌ Error during task registration: {e}")


if __name__ == "__main__":
    celery_app.start()
