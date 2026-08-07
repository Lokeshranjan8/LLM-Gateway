# LLM Gateway

A production-style **FastAPI LLM Gateway** that routes chat requests to upstream
LLM providers with enterprise-grade resilience patterns:

- **Smart provider routing** with automatic **fallback** when the primary provider fails
- **Circuit breaker** per provider (`CLOSED → OPEN → HALF_OPEN`) to stop hammering unhealthy providers
- **Retry logic** for transient failures (timeouts, connection errors, HTTP 5xx)
- **Redis-backed token-bucket rate limiting** (atomic Lua script, per-client IP)
- **Pluggable provider adapters** behind a shared abstract contract
- **Fully containerized** with Docker Compose + healthchecks

---

## Architecture

### How a request flows through the system

```mermaid
flowchart TD
    Client[Client] -->|POST /v1/chat| Gateway

    subgraph Gateway["FastAPI Gateway (gateway/)"]
        direction TB
        API[API Layer<br/>app/api/chat.py]
        RateLimit[Rate Limiter<br/>app/rate_limit/token_bucket.py]
        Router[Provider Router<br/>app/router/router.py]
        CircuitA[Circuit Breaker<br/>Mock A]
        CircuitB[Circuit Breaker<br/>Mock B]
        AdapterA[Provider Adapter<br/>MockProviderA]
        AdapterB[Provider Adapter<br/>MockProviderB]
        Retry[Retry Helper<br/>app/retry.py]

        API --> RateLimit
        RateLimit -->|429 Too Many Requests| API
        RateLimit --> Router
        Router -->|primary| CircuitA
        Router -->|primary| CircuitB
        Router -->|fallback| CircuitA
        Router -->|fallback| CircuitB
        CircuitA --> AdapterA
        CircuitB --> AdapterB
        AdapterA --> Retry
        AdapterB --> Retry
    end

    subgraph Infrastructure["Infrastructure"]
        Redis[(Redis<br/>token bucket)]
        ProviderA[Mock Provider A<br/>mock_provider_a/]
        ProviderB[Mock Provider B<br/>mock_provider_b/]
    end

    RateLimit -.->|Lua script| Redis
    Retry -->|HTTP /chat| ProviderA
    Retry -->|HTTP /chat| ProviderB

    ProviderA -->|response| Retry
    ProviderB -->|response| Retry
    Retry -->|ChatResponse| AdapterA
    AdapterA --> CircuitA
    CircuitA --> Router
    Router -->|ChatResponse| API
    API -->|200 OK| Client

    style Gateway fill:#1f2937,stroke:#6366f1,stroke-width:2px,color:#fff
    style Infrastructure fill:#111827,stroke:#10b981,stroke-width:2px,color:#fff
    style Client fill:#0f172a,stroke:#f59e0b,stroke-width:2px,color:#fff
    style Redis fill:#0f172a,stroke:#f59e0b,stroke-width:2px,color:#fff
```

### Architecture diagram

```
┌──────────┐   POST /v1/chat   ┌──────────────────────────────────────────────────────────────┐
│  Client  │ ─────────────────▶ │                         FASTAPI GATEWAY                        │
└──────────┘                    │                                                                │
                                │  ┌────────────────────┐      ┌──────────────────────────┐      │
                                │  │   API Layer        │      │   Rate Limiter           │      │
                                │  │   api/chat.py      │ ───▶ │   token_bucket.py        │      │
                                │  └────────────────────┘      └────────────┬─────────────┘      │
                                │                                          │ allowed?             │
                                │                                          ▼ (yes)                │
                                │        ┌─────────────────────────────────┘   (no → 429)         │
                                │        ▼                                                       │
                                │  ┌────────────────────┐                                       │
                                │  │  Provider Router   │  primary / fallback                    │
                                │  │  router/router.py  │                                       │
                                │  └─────┬────────┬─────┘                                       │
                                │        │        │                                              │
                                │        ▼        ▼                                              │
                                │  ┌──────────┐ ┌──────────┐                                    │
                                │  │ Circuit  │ │ Circuit  │  CLOSED / OPEN / HALF_OPEN          │
                                │  │ Breaker A│ │ Breaker B│                                    │
                                │  └────┬─────┘ └────┬─────┘                                    │
                                │       │            │                                           │
                                │       ▼            ▼                                           │
                                │  ┌──────────┐ ┌──────────┐                                    │
                                │  │ Adapter  │ │ Adapter  │  BaseProvider contract              │
                                │  │ Mock A   │ │ Mock B   │                                    │
                                │  └────┬─────┘ └────┬─────┘                                    │
                                │       │            │                                           │
                                │       └─────┬──────┘                                           │
                                │             ▼                                                  │
                                │  ┌────────────────────┐                                       │
                                │  │   Retry Helper      │   max 2 retries on 5xx/timeout        │
                                │  │   retry.py          │                                       │
                                │  └─────────┬──────────┘                                       │
                                └────────────┼───────────────────────────────────────────────────┘
                                             │ HTTP /chat
                                             ▼
                        ┌────────────────────────────────────────────┐
                        │                DOCKER NETWORK               │
                        │                                            │
                        │  ┌──────────────────┐ ┌──────────────────┐ │
                        │  │ Mock Provider A  │ │ Mock Provider B  │ │
                        │  │ mock_provider_a/ │ │ mock_provider_b/ │ │
                        │  └──────────────────┘ └──────────────────┘ │
                        └────────────────────────────────────────────┘
                                             │
                                             ▼
                        ┌────────────────────────────────────────────┐
                        │                   REDIS                     │
                        │   token-bucket Lua script (atomic, per-IP)  │
                        └────────────────────────────────────────────┘
```

---


## 📁 Project Structure

```
llm-gateway/
├── docker-compose.yml              # Orchestrates redis + providers + gateway
├── gateway/                        # The LLM Gateway service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # FastAPI entry point (/health, mounts /v1)
│       ├── config.py               # Pydantic settings (env-driven)
│       ├── schemas.py              # ChatRequest / ChatResponse models
│       ├── cache.py                # Redis client + get/set cache helpers
│       ├── circuit_breaker.py      # Per-provider circuit breaker state machine
│       ├── retry.py                # Retry helper for provider calls
│       ├── api/
│       │   └── chat.py             # POST /v1/chat endpoint + rate limiting
│       ├── providers/
│       │   ├── base.py             # Abstract BaseProvider contract
│       │   ├── mock_a.py           # Adapter for Mock Provider A
│       │   └── mock_b.py           # Adapter for Mock Provider B
│       ├── rate_limit/
│       │   └── token_bucket.py     # Redis token-bucket (atomic Lua script)
│       └── router/
│           └── router.py           # Primary/fallback selection + circuit logic
├── mock_provider_a/                # Mock LLM provider A (standalone FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                     # /chat → {"provider": "mock_a", ...}
└── mock_provider_b/                # Mock LLM provider B (standalone FastAPI)
    ├── Dockerfile
    ├── requirements.txt
    └── main.py                     # /chat → {"provider": "mock_b", ...}
```

---

## Quick Start

### With Docker Compose (recommended)

```bash
docker compose up --build
```

This starts **four** services with healthchecks:

| Service             | Port        | Purpose                                   |
| ------------------- | ----------- | ----------------------------------------- |
| `gateway`           | `8000`      | LLM Gateway API                           |
| `mock-provider-a`   | internal    | Mock LLM provider A                       |
| `mock-provider-b`   | internal    | Mock LLM provider B                       |
| `redis`             | internal    | Token-bucket rate limiting                |

The gateway is available at `http://localhost:8000` and its health endpoint is
`GET /health`.

### Run locally (without Docker)

From the `gateway/` directory:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

> **Note:** The default provider URLs point to Docker Compose service names
> (`http://mock-provider-a:8000`). For a fully local run, override them with
> environment variables, e.g. `PROVIDER_A_URL=http://localhost:9001` and
> `PROVIDER_B_URL=http://localhost:9002`, and make sure Redis is reachable.

---
