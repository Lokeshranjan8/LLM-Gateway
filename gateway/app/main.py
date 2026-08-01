"""FastAPI application entry point."""

from fastapi import FastAPI
from app.api.chat import router as chat_router



app = FastAPI()
app.include_router(chat_router, prefix="/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
