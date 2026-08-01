# LLM Gateway

Starter structure for a FastAPI gateway that routes chat requests to mock LLM providers.

Start all services with Docker:

```bash
docker compose up --build
```

The gateway is available at `http://localhost:8000`; its health endpoint is
`GET /health`.

Run the gateway from `gateway/`:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Send a request to `POST /v1/chat`:

```json
{"message": "Hello", "provider": "mock_a"}
```

Use `"mock_b"` to send the request to Mock Provider B instead. The gateway
chooses the provider, then calls that service over Docker's internal network.
