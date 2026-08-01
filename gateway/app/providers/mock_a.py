"""Gateway adapter for the separate Mock Provider A container."""

import requests

from app.config import settings
from app.providers.base import BaseProvider
from app.schemas import ChatRequest, ChatResponse


class MockProviderA(BaseProvider):

    async def chat(self, request: ChatRequest) -> ChatResponse:
        # Inside Docker, this reaches the `mock-provider-a` service.
        response = requests.post(
            f"{settings.provider_a_url}/chat",
            json={"message": request.message},
            timeout=10,
        )

        # Raise an error if Mock A returned an HTTP error, then read its JSON.
        response.raise_for_status()
        return ChatResponse.model_validate(response.json())
