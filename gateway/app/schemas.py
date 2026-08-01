"""Request and response models."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    provider: str = "mock_a"


class ChatResponse(BaseModel):
    provider: str
    message: str


