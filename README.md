# LLM Gateway

## Overview
A production‑style **FastAPI LLM Gateway** that routes chat requests to upstream LLM providers while applying enterprise‑grade resilience patterns:
- Smart provider routing with automatic fallback
- Per‑provider circuit breaker (`CLOSED → OPEN → HALF_OPEN`)
- Retry logic for transient failures (timeouts, connection errors, HTTP 5xx)
- Redis‑backed token‑bucket rate limiting (atomic Lua script, per‑client IP)
- Pluggable provider adapters behind a shared abstract contract
- Fully containerised with Docker Compose and health‑checks

The gateway ships with two mock LLM providers (`mock_provider_a` and `mock_provider_b`) that you can replace with real services (e.g., Groq) by implementing the `BaseProvider` interface.

## Tech Stack
- **Python 3.12** – core language
- **FastAPI** – HTTP API framework
- **Uvicorn** – ASGI server
- **Redis** – token‑bucket storage and atomic Lua script
- **Docker & Docker Compose** – containerisation and orchestration
- **Pydantic Settings** – environment‑driven configuration
- **Prometheus client** – metrics endpoint (ready for scraping)

## Project Structure
```
llm-gateway/
├── docker-compose.yml              # Orchestrates Redis, mock providers and the gateway
├── .env.example                    # Template for required environment variables
├── gateway/                        # The LLM Gateway service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # FastAPI entry point (`/health`, mounts `/v1`)
│       ├── config.py               # Pydantic settings (env‑driven)
│       ├── schemas.py              # Request / response models
│       ├── cache.py                # Redis client helpers
│       ├── circuit_breaker.py      # Circuit‑breaker state machine
│       ├── retry.py                # Retry helper
│       ├── api/
│       │   └── chat.py             # `POST /v1/chat` endpoint + rate limiting
│       ├── providers/
│       │   ├── base.py             # Abstract `BaseProvider` contract
│       │   ├── mock_a.py           # Adapter for Mock Provider A
│       │   └── mock_b.py           # Adapter for Mock Provider B
│       ├── rate_limit/
│       │   └── token_bucket.py     # Redis token‑bucket implementation
│       └── router/
│           └── router.py           # Primary/fallback selection + circuit logic
├── mock_provider_a/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                     # Simple `/chat` endpoint returning provider A tag
├── mock_provider_b/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                     # Simple `/chat` endpoint returning provider B tag
```

## Configuration
Environment variables drive the gateway behaviour. Copy `.env.example` to `.env` (which is ignored by Git) and adjust values as needed.

| Variable | Description | Default |
|----------|-------------|---------|
| `CIRCUIT_FAILURE_THRESHOLD` | Number of consecutive failures before opening the circuit breaker | `3` |
| `CIRCUIT_COOLDOWN_SECONDS` | Cool‑down period (seconds) before attempting a half‑open state | `10` |
| `GROQ_API_KEY` | API key for the Groq LLM provider (keep secret) | – |
| `GROQ_MODEL` | Model name to use with Groq | `llama-3.3-70b-versatile` |
| `TOKEN_BUCKET_CAPACITY` | Maximum tokens per bucket (per client IP) | `1000` |
| `REFILL_RATE` | Tokens added per second | `600` |
| `RATE_LIMIT_KEY_PREFIX` | Prefix for Redis keys used by the rate limiter | `rate_limit` |
| `REDIS_URL` | Redis connection string (set automatically in Docker Compose) | `redis://redis:6379/0` |

The gateway reads these variables via **pydantic‑settings**, so they can also be supplied directly in the environment or an `.env` file.

## Quick Start

### Using Docker Compose (recommended)
```bash
# Build images and start all services
docker compose up --build
```
Docker Compose will launch:

| Service | Port | Purpose |
|---------|------|---------|
| `gateway` | `8000` | LLM Gateway API |
| `mock-provider-a` | internal | Mock Provider A |
| `mock-provider-b` | internal | Mock Provider B |
| `redis` | internal | Token‑bucket store |

Health checks are defined for each service; the compose command returns only when all are healthy.
- **Gateway health**: `GET http://localhost:8000/health`
- **Chat