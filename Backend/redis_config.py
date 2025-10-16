
import os
import redis
from dotenv import load_dotenv


load_dotenv()


redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", "6379"))

print(f"🔧 Using Redis at {redis_host}:{redis_port}")

def get_redis_client() -> redis.Redis:
    """
    Get Redis client configured for local Docker Redis
    """
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=False
    )
