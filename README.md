# LLM Gateway

## Overview

**LLM Gateway** is a production‑style FastAPI service that forwards chat requests to upstream LLM providers while applying enterprise‑grade resilience patterns:

- **Smart provider routing** with automatic fallback when the primary provider fails
- **Circuit breaker** per provider (`CLOSED → OPEN → HALF_OPEN`) to stop hammering unhealthy services
- **Retry logic** for transient errors (timeouts, connection errors, HTTP 5xx)
- **Redis‑backed token‑bucket rate limiting** (atomic Lua script, per‑client IP)
- **Pluggable provider adapters** behind a shared abstract contract
- Fully containerised with Docker Compose and health‑checks

The gateway ships with two mock providers (`mock_provider_a` and `mock_provider_b`) that emulate real LLM APIs, making it easy to test routing, circuit breaking and rate limiting locally.

---

## Quick Start

### With Docker Compose (recommended)
```bash
# Copy the example env file and fill in your Groq key
cp .env.example .env
# Edit .env if you want to change defaults

docker compose up --build
```

The compose file starts four services:

| Service | Port | Purpose |
|---------|------|---------|
| `gateway` | `8000` | LLM Gateway API |
| `mock-provider-a` | internal | Mock LLM provider A |
| `mock-provider-b` | internal | Mock LLM provider B |
| `redis` | internal | Token‑bucket rate limiting |

The gateway health endpoint is reachable at `http://localhost:8000/health` and the chat endpoint at `http://localhost:8000/v1/chat`.

### Run the gateway locally (without Docker)
```bash
# From the repository root
cd gateway
pip install -r requirements.txt
uvicorn app.main:app --reload
```

> **Note**: When running locally you must point the provider URLs to reachable endpoints (e.g. `http://localhost:9001` and `http://localhost:9002`) and have a Redis instance available. The default URLs are the Docker Compose service names, so they work out‑of‑the‑box only inside the compose network.

---

## Tech Stack
- **Python 3.12** – core language
- **FastAPI** – HTTP API framework
- **Uvicorn** – ASGI server
- **Redis** – token‑bucket rate limiting (Lua script for atomicity)
- **Docker & Docker Compose** – containerisation and orchestration
- **Groq LLM provider** – real LLM backend (optional, configured via env vars)
- **Prometheus client** – metrics exposition (ready for scraping)

---

## Project Structure
```
llm-gateway/
├── .env.example                     # Example environment variables
├── docker-compose.yml                # Orchestrates redis, mock providers & gateway
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
│       │   └── token_bucket.py     # Redis token‑bucket implementation
│       └── router/
│           └── router.py           # Primary/fallback selection + circuit logic
├── mock_provider_a/                  # Simple FastAPI mock LLM provider A
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
└── mock_provider_b/                  # Simple FastAPI mock LLM provider B
    ├── Dockerfile
    ├── requirements.txt
    └── main.py
```

---

## Configuration

The gateway reads its configuration from environment variables. An example file is provided at **`.env.example`**:

```dotenv
# Gateway circuit breaker settings
CIRCUIT_FAILURE_THRESHOLD=3          # Failures before opening the circuit
CIRCUIT_COOLDOWN_SECONDS=10          # Cool‑down period before half‑open state

# Groq LLM provider (keep the real key out of version control)
GROQ_API_KEY=                         # <-- set your Groq API key here
GROQ_MODEL=llama-3.3-70b-versatile   # Model to use when calling Groq

# Redis token‑bucket rate limiting
TOKEN_BUCKET_CAPACITY=1000           # Max tokens per bucket
REFILL_RATE=600                       # Tokens added per second
RATE_LIMIT_KEY_PREFIX=rate_limit     # Prefix for Redis keys
```

All variables have sensible defaults defined in `gateway/app/config.py`. You can override any of them by editing `.env` or by passing them directly to Docker Compose, e.g.:
```bash
CIRCUIT_FAILURE_THRESHOLD=5 docker compose up --build
```

---

## Running the Project

### Docker Compose (full stack)
1. **Create an `.env` file** from the example and add your Groq key if you intend to use the real provider.
2. **Start the stack**:
   ```bash
   docker compose up --build
   ```
3. **Verify health**:
   ```bash
   curl http://localhost:8000/health
   ```
4. **Send a chat request** (example using `curl`):
   ```bash
   curl -X POST http://localhost:8000/v1/chat \
        -H "Content-Type: application/json" \
        -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
   ```

### Local Development (gateway only)
```bash
cd gateway
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Make sure a Redis instance is reachable (default `redis://localhost:6379/0`).

---

## Key Dependencies
| Package | Version (minimum) | Purpose |
|---------|-------------------|---------|
| fastapi | >=0.115.0 | API framework |
| uvicorn | >=0.30.0 | ASGI server |
| pydantic-settings | >=2.0.0 | Typed settings from env vars |
| requests | >=2.32.0 | HTTP calls to upstream providers |
| redis | >=5.0.0 | Token‑bucket storage & Lua scripting |
| prometheus-client | (no version pinned) | Metrics exposition |

---

## Contributing
Contributions are welcome! Follow these steps:

1. **Fork the repository** and clone your fork.
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**. Keep the existing project structure and add unit tests where appropriate.
4. **Run the test suite** (if added) and ensure the Docker Compose stack still starts cleanly:
   ```bash
   docker compose up --build --exit-code-from gateway
   ```
5. **Submit a Pull Request** with a clear description of the change.

Please keep the following in mind:
- Do not commit real secrets; use the `.env.example` pattern.
- Update the README if you add new configuration options or services.
- Follow the existing coding style (type hints, Pydantic models, docstrings).

---

*Happy hacking!*