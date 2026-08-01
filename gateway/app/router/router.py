"""Choose which provider should receive a chat request."""

from app.providers.mock_a import MockProviderA
from app.providers.mock_b import MockProviderB
from app.schemas import ChatRequest, ChatResponse


class ProviderRouter:
    def __init__(self) -> None:
        self.providers = {"mock_a": MockProviderA(), "mock_b": MockProviderB()}

    async def chat(self, request: ChatRequest) -> ChatResponse:
        # `request.provider` is "mock_a" or "mock_b".
        # If it is missing/unknown, use Mock A as the simple default.
        provider = self.providers.get(request.provider, self.providers["mock_a"])
        return await provider.chat(request)
