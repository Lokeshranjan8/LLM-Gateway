"""Redis token-bucket rate limiter.

The Lua script runs atomically inside Redis. This prevents two requests from
reading the same remaining token and both being allowed.
"""

from fastapi import HTTPException
import redis

from app.cache import redis_client
from app.config import settings


TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local ttl = tonumber(ARGV[3])

-- Use Redis server time so every gateway instance uses the same clock.
local redis_time = redis.call('TIME')
local now = tonumber(redis_time[1]) + (tonumber(redis_time[2]) / 1000000)

local tokens = tonumber(redis.call('HGET', key, 'tokens'))
local last_refill = tonumber(redis.call('HGET', key, 'last_refill'))

-- A new client starts with a full bucket.
if tokens == nil then
    tokens = capacity
    last_refill = now
end

-- Refill according to time passed, but never exceed capacity.
local elapsed = math.max(0, now - last_refill)
tokens = math.min(capacity, tokens + (elapsed * refill_rate))

local allowed = 0
local retry_after = 0

if tokens >= 1 then
    tokens = tokens - 1
    allowed = 1
else
    retry_after = math.ceil((1 - tokens) / refill_rate)
end

redis.call('HSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', key, ttl)

-- Strings preserve decimal token values in Redis/Python responses.
return {allowed, tostring(tokens), tostring(retry_after)}
"""


class TokenBucket:
    def __init__(self) -> None:
        self.capacity = settings.token_bucket_capacity
        self.refill_rate = settings.refill_rate
        self.key_prefix = settings.rate_limit_key_prefix

        # Remove inactive client buckets after they have time to refill.
        self.ttl_seconds = max(1, int((self.capacity / self.refill_rate) * 2))
        self.run_bucket = redis_client.register_script(TOKEN_BUCKET_LUA)

    def check_rate_limit(self, client_id: str) -> dict:
        """Return whether this client may make one request now."""
        key = f"{self.key_prefix}:{client_id}"

        try:
            result = self.run_bucket(
                keys=[key],
                args=[self.capacity, self.refill_rate, self.ttl_seconds],
            )

            allowed = bool(int(result[0]))
            remaining_tokens = float(result[1])
            retry_after = int(float(result[2]))

            return {
                "allowed": allowed,
                "remaining_tokens": remaining_tokens,
                "retry_after": retry_after,
            }

        except redis.RedisError as error:
            print(f"Redis rate limit failed: {str(error)}")
            # Fail closed: do not allow paid LLM traffic without rate limiting.
            raise HTTPException(
                status_code=503,
                detail="Rate limit service is temporarily unavailable.",
            )
