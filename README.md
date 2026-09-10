# LLM Gateway

## Overview
A production‑style **FastAPI LLM Gateway** that routes chat requests to upstream LLM providers while applying enterprise‑grade resilience patterns:

- **Smart provider routing** with automatic fallback when the primary provider fails
- **Circuit breaker** per provider (`CLOSED → OPEN → HALF_OPEN`) to stop hammering unhealthy providers
- **Retry logic** for transient failures (timeouts, connection errors, HTTP 5xx)
- **Redis‑backed token‑bucket rate limiting** (atomic Lua script, per‑client IP)
- **Pluggable provider adapters** behind a shared abstract contract
- **Fully containerized** with Docker Compose + health‑checks

The gateway ships with two mock providers (`mock_provider_a` and `mock_provider_b`) that emulate real LLM services, making it easy to test routing, circuit‑breaker, and rate‑limit behaviour locally.

---

## Tech Stack
| Layer | Technology |
|-------|------------|
| API framework | **FastAPI** (≥0.115) |
| ASGI server | **Uvicorn** (≥0.30) |
| Configuration | **pydantic‑settings** (≥2.0) |
| HTTP client | **requests** (≥2.32) |
| Rate limiting & caching | **Redis** (via `redis` Python client ≥5.0) |
| Metrics | **prometheus‑client** |
| Containerisation | **Docker** + **Docker Compose** |
| Mock providers | Simple FastAPI services |

---

## Project Structure
```
llm-gateway/
├── .env.example                     # Template for environment variables
├── docker-compose.yml               # Orchestrates Redis, mock providers & gateway
├── gateway/                         # The LLM Gateway service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # FastAPI entry point (health + /v1 router)
│       ├── config.py               # Pydantic Settings (env‑driven)
│       ├── schemas.py              # Request / response models
│       ├── cache.py                # Redis client helpers
│       ├── circuit_breaker.py      # Per‑provider circuit‑breaker state machine
│       ├── retry.py                # Retry helper for provider calls
│       ├── api/
│       │   └── chat.py             # POST /v1/chat endpoint + rate limiting
│       ├── providers/
│       │   ├── base.py             # Abstract BaseProvider contract
│       │   ├── mock_a.py           # Adapter for Mock Provider A
│       │   └── mock_b.py           # Adapter for Mock Provider B
│       ├── rate_limit/
│       │   └── token_bucket.py     # Redis token‑bucket (atomic Lua script)
│       └── router/
│           └── router.py           # Primary/fallback selection + circuit logic
├── mock_provider_a/                 # Simple FastAPI mock LLM provider A
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                     # /chat → {"provider": "mock_a", ...}
└── mock_provider_b/                 # Simple FastAPI mock LLM provider B
    ├── Dockerfile
    ├── requirements.txt
    └── main.py                     # /chat → {"provider": "mock_b", ...}
```

---

## Configuration
All configurable values are read from environment variables. A template is provided in **`.env.example`** – copy it to `.env` (which is ignored by Git) and fill in the real values.

| Variable | Description | Default |
|----------|-------------|---------|
| `CIRCUIT_FAILURE_THRESHOLD` | Number of consecutive failures before a circuit opens | `3` |
| `CIRCUIT_COOLDOWN_SECONDS` | Cool‑down period (seconds) before a circuit attempts to half‑open | `10` |
| `GROQ_API_KEY` | API key for the Groq LLM provider (keep secret) | – |
| `GROQ_MODEL` | Model name to request from Groq | `llama-3.3-70b-versatile` |
| `TOKEN_BUCKET_CAPACITY` | Maximum tokens per bucket (per client IP) | `1000` |
| `REFILL_RATE` | Tokens added per second | `600` |
| `RATE_LIMIT_KEY_PREFIX` | Prefix for Redis keys used by the rate limiter | `rate_limit` |
| `REDIS_URL` | Redis connection string – set automatically by Docker Compose | `redis://redis:6379/0` |

The gateway reads these variables via **pydantic‑settings**, so you can also override them at runtime (e.g., `CIRCUIT_FAILURE_THRESHOLD=5 docker compose up`).

---

## Quick Start
### 1. Using Docker Compose (recommended)
```bash
# Copy the env template and add your Groq key (if you plan to use the real provider)
cp .env.example .env
# Edit .env as needed
nano .env

# Build and start all services
docker compose up --build
```
The compose file starts four containers:
| Service | Port | Purpose |
|---------|------|---------|
| `gateway` | `8000` (host) | LLM Gateway API |
| `mock-provider-a` | internal | Mock LLM Provider A |
| `mock-provider-b` | internal | Mock LLM Provider B |
| `redis` | internal | Token‑bucket store |

*Health checks* ensure each container is ready before the gateway begins accepting traffic.

**Test the gateway**
```bash
curl -X POST http://localhost:8000/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```
You should receive a JSON response that includes the selected provider.

### 2. Running the Gateway Locally (no Docker)
```bash
# 1️⃣ Start a Redis instance (Docker is the easiest way)
docker run -d --name local-redis -p 6379:6379 redis:7-alpine

# 2️⃣ Install Python dependencies
cd gateway
pip install -r requirements.txt

# 3️⃣ Export required env vars (or copy .env.example → .env and `export $(cat .env | xargs)`) 
export REDIS_URL=redis://localhost:6379/0
# ...other vars as needed

# 4️⃣ Run the API
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
When running locally you must point the mock providers to reachable URLs (e.g., `PROVIDER_A_URL=http://localhost:9001`). The Docker‑compose version already wires the correct service names, so the local mode is mainly useful for debugging.

---

## Running the Project
| Command | What it does |
|---------|--------------|
| `docker compose up --build` | Build images (if needed) and start the full stack |
| `docker compose down` | Stop and remove containers, networks, and volumes |
| `docker compose logs -f gateway` | Stream gateway logs |
| `docker compose exec gateway /bin/bash` | Open a shell inside the running gateway container |
| `pytest` *(if tests are added later)* | Run unit/integration tests |

---

## Key Dependencies
- **fastapi** – modern, high‑performance web framework
- **uvicorn[standard]** – ASGI server with HTTP/2 and websockets support
- **pydantic-settings** – type‑safe environment configuration
- **requests** – simple HTTP client used by provider adapters
- **redis** – Redis client for token‑bucket rate limiting
- **prometheus-client** – expose `/metrics` for observability (not covered in the README but present in the codebase)

---

## Contributing
Contributions are welcome! Follow these steps to get started:
1. **Fork** the repository and clone your fork.
2. Create a feature branch: `git checkout -b feat/your‑feature`.
3. Make your changes. Keep the existing coding style (PEP 8) and add or update tests where applicable.
4. Run the test suite (if present) and ensure the Docker Compose stack still starts cleanly.
5. Submit a **Pull Request** with a clear description of what you changed and why.

When adding new environment variables, remember to:
- Document them in this README under **Configuration**.
- Add a default (or sensible fallback) in `gateway/app/config.py`.
- Update `.env.example` so new contributors know the required keys.

---

## Contact & Support
If you encounter issues or have questions about the architecture, feel free to open an issue on the repository. Happy coding!
