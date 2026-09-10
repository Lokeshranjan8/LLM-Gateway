# LLM Gateway

## Overview
A production‑style **FastAPI LLM Gateway** that routes chat requests to upstream LLM providers while applying enterprise‑grade resilience patterns:

- **Smart provider routing** with automatic fallback when the primary provider fails
- **Circuit breaker** per provider (`CLOSED → OPEN → HALF_OPEN`) to stop hammering unhealthy providers
- **Retry logic** for transient failures (timeouts, connection errors, HTTP 5xx)
- **Redis‑backed token‑bucket rate limiting** (atomic Lua script, per‑client IP)
- **Pluggable provider adapters** behind a shared abstract contract
- **Fully containerized** with Docker Compose + health‑checks

The gateway ships with two mock LLM providers (`mock_provider_a` and `mock_provider_b`) that you can replace with real services (e.g., Groq) by implementing the `BaseProvider` contract.

---

## Tech Stack
- **Python 3.12**
- **FastAPI** – high‑performance API framework
- **Uvicorn** – ASGI server
- **Redis** – token‑bucket storage & atomic Lua script
- **Docker & Docker Compose** – reproducible multi‑service environment
- **Pydantic Settings** – environment‑driven configuration
- **Prometheus client** – metrics endpoint (exposed by FastAPI)

---

## Quick Start
### Using Docker Compose (recommended)
```bash
# Copy the example env file and fill in your secrets
cp .env.example .env
# Edit .env – add your GROQ_API_KEY if you want to use the real provider

# Build and start all services
docker compose up --build
```
The compose file starts four services with health‑checks:
| Service | Port | Purpose |
|---|---|---|
| `gateway` | `8000` | LLM Gateway API |
| `mock-provider-a` | internal | Mock LLM provider A |
| `mock-provider-b` | internal | Mock LLM provider B |
| `redis` | internal | Token‑bucket store |

The gateway health endpoint is reachable at `http://localhost:8000/health` and the chat endpoint at `http://localhost:8000/v1/chat`.

### Running the gateway locally (without Docker)
```bash
# From the repository root
cd gateway
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Ensure Redis is running locally (e.g., `docker run -p 6379:6379 redis:7-alpine`)
uvicorn app.main:app --reload
```
> **Tip:** When running locally you must point the provider URLs to reachable endpoints (e.g., `PROVIDER_A_URL=http://localhost:9001`). The default URLs are the Docker service names used in compose.

---

## Project Structure
```
llm-gateway/
├── .env.example                     # Template for environment variables
├── docker-compose.yml                # Orchestrates Redis, mock providers, gateway
├── gateway/                          # The LLM Gateway service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # FastAPI entry point (health + /v1 router)
│       ├── config.py               # Pydantic Settings (env‑driven)
│       ├── schemas.py              # Request / response models
│       ├── cache.py                # Redis client helpers
│       ├── circuit_breaker.py      # Circuit‑breaker state machine
│       ├── retry.py                # Retry helper for provider calls
│       ├── api/
│       │   └── chat.py             # POST /v1/chat endpoint + rate limiting
│       ├── providers/
│       │   ├── base.py             # Abstract BaseProvider contract
│       │   ├── mock_a.py           # Adapter for Mock Provider A
│       │   └── mock_b.py           # Adapter for Mock Provider B
│       ├── rate_limit/
│       │   └── token_bucket.py     # Redis token‑bucket (Lua script)
│       └── router/
│           └── router.py           # Primary/fallback selection + circuit logic
├── mock_provider_a/                  # Simple FastAPI mock provider
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
└── mock_provider_b/                  # Simple FastAPI mock provider
    ├── Dockerfile
    ├── requirements.txt
    └── main.py
```

---

## Configuration
All configurable values are loaded from environment variables (via `pydantic-settings`). A template is provided in `.env.example`.

| Variable | Default | Description |
|---|---|---|
| `CIRCUIT_FAILURE_THRESHOLD` | `3` | Number of consecutive failures before a circuit opens |
| `CIRCUIT_COOLDOWN_SECONDS` | `10` | Cool‑down period before a circuit attempts to half‑open |
| `GROQ_API_KEY` | *(empty)* | API key for the Groq LLM provider – **keep secret** in an untracked `.env` |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Model name used when calling Groq |
| `TOKEN_BUCKET_CAPACITY` | `1000` | Maximum tokens per bucket (per client IP) |
| `REFILL_RATE` | `600` | Tokens added per second |
| `RATE_LIMIT_KEY_PREFIX` | `rate_limit` | Prefix for Redis keys storing token buckets |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string (used by the gateway) |

You can override any of these values in the `docker-compose.yml` `environment:` block or by exporting them before running the container.

---

## Running the Project
1. **Prepare the environment** – copy `.env.example` to `.env` and fill in any secrets.
2. **Start services** – `docker compose up --build` (or use the local‑run steps above).
3. **Verify health** – `curl http://localhost:8000/health` should return `{"status":"ok"}`.
4. **Send a chat request**:
   ```bash
   curl -X POST http://localhost:8000/v1/chat \
        -H "Content-Type: application/json" \
        -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
   ```
   The gateway will route the request to the primary mock provider, apply rate‑limiting, circuit‑breaker checks, and fallback to the secondary provider if needed.

---

## Key Dependencies
- **fastapi** – API framework (`>=0.115.0`)
- **uvicorn[standard]** – ASGI server (`>=0.30.0`)
- **pydantic-settings** – Settings management (`>=2.0.0`)
- **requests** – HTTP client for provider calls (`>=2.32.0`)
- **redis** – Redis client (`>=5.0.0`)
- **prometheus-client** – Metrics exposition

---

## Contributing
Contributions are welcome! Follow these steps:
1. Fork the repository and clone your fork.
2. Create a feature branch: `git checkout -b feat/your-feature`.
3. Keep the code style consistent with the existing project (PEP 8, type hints).
4. Add or update tests if you introduce new functionality.
5. Ensure all services start cleanly with `docker compose up --build` and that the health checks pass.
6. Open a Pull Request describing the change and referencing any related issue.

---

*Happy hacking!*