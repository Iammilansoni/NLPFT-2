"""
Redis Configuration - Centralized Redis client factory
All configuration loaded from environment via config.py
"""

import redis
from app.core.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

print(f"Using Redis at {REDIS_HOST}:{REDIS_PORT}")

def get_redis_client() -> redis.Redis:
    """
    Get Redis client configured from environment variables
    """
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=False
    )
