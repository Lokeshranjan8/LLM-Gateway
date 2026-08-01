"""Small shared contract for every provider adapter."""

from abc import ABC, abstractmethod

from app.schemas import ChatRequest, ChatResponse


class BaseProvider(ABC):
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send the message to one provider and return its answer."""
