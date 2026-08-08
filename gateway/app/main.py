"""FastAPI application entry point."""

from fastapi import FastAPI
from app.api.chat import router as chat_router
from prometheus_client import make_asgi_app
from app import metrics

app = FastAPI()
app.include_router(chat_router, prefix="/v1")
app.mount("/metrics", make_asgi_app())


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/")
async def root()-> dict[str, str]:
    return {"message":"LLM gateway running fine"}
