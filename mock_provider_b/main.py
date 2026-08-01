from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock Provider B")


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, str]:
    return {"provider": "mock_b", "message": f"Mock B: {request.message}"}
