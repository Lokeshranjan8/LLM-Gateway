"""One place for addresses the gateway needs."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # These names are Docker Compose service names, not localhost.
    provider_a_url: str = "http://mock-provider-a:8000"
    provider_b_url: str = "http://mock-provider-b:8000"


settings = Settings()
