"""One place for addresses the gateway needs."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # These names are Docker Compose service names, not localhost.
    provider_a_url: str = "http://mock-provider-a:8000"
    provider_b_url: str = "http://mock-provider-b:8000"

    # Circuit breaker values can be changed with environment variables.
    circuit_failure_threshold: int = 3
    circuit_cooldown_seconds: int = 10

    # Token bucket rate-limit configuration.
    token_bucket_capacity: int = 6
    refill_rate: int = 1
    rate_limit_key_prefix: str = "rate_limit"

settings = Settings()
