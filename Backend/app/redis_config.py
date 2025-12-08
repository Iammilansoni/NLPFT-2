
import os
import redis
from dotenv import load_dotenv


load_dotenv()


redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
redis_password = os.getenv("REDIS_PASSWORD", "nlpforge_redis_secure_password_2024")

print(f"Using Redis at {redis_host}:{redis_port}")

def get_redis_client() -> redis.Redis:
    """
    Get Redis client configured for local Docker Redis
    """
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=False
    )
