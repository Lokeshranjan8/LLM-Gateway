import json
import os

import redis

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(
    redis_url,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def get_cache(key: str):
    try:
        cache_data = redis_client.get(key)
        if cache_data:
            print(f"cache hit for key :{key}")
            return json.loads(cache_data)
        return None

    except redis.RedisError as error:
        print(f"Redis cache read failed: {str(error)}")
        return None


def set_cache(key: str, value, expire: int = 30) -> None:
    try:
        redis_client.set(key, json.dumps(value), ex=expire)
    except redis.RedisError as error:
        print(f"Redis cache write failed: {str(error)}")
