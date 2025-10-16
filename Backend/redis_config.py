
import os
import redis

USERNAME = os.getenv("REDIS_USERNAME")
PASSWORD = os.getenv("REDIS_PASSWORD")
HOST = "redis-18922.c212.ap-south-1-1.ec2.redns.redis-cloud.com"
PORT = 18922

def get_redis_client():
    return redis.Redis(
        host=HOST,
        port=PORT,
        username=USERNAME,
        password=PASSWORD,
        decode_responses=False,
        ssl=True,
        ssl_cert_reqs=None
    )
