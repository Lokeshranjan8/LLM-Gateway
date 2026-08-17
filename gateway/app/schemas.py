"""Request and response models."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    provider: str = "groq"


class ChatResponse(BaseModel):
    provider: str
    message: str

