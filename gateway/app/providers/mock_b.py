"""Gateway adapter for the separate Mock Provider B container."""

from app.config import settings
from app.providers.base import BaseProvider
from app.retry import call_provider
from app.schemas import ChatRequest, ChatResponse


class MockProviderB(BaseProvider):
    async def chat(self, request: ChatRequest) -> ChatResponse:
        data = call_provider(
            provider_name="Mock B",
            url=f"{settings.provider_b_url}/chat",
            message=request.message,
        )
        return ChatResponse.model_validate(data)
