"""Gateway adapter for the separate Mock Provider B container."""

import requests

from app.config import settings
from app.providers.base import BaseProvider
from app.schemas import ChatRequest, ChatResponse


class MockProviderB(BaseProvider):

    async def chat(self, request: ChatRequest) -> ChatResponse:
        # Inside Docker, this reaches the `mock-provider-b` service.
        response = requests.post(
            f"{settings.provider_b_url}/chat",
            json={"message": request.message},
            timeout=10,
        )

        # Raise an error if Mock B returned an HTTP error, then read its JSON.
        response.raise_for_status()
        return ChatResponse.model_validate(response.json())
