"""Choose which provider should receive a chat request."""

from fastapi import HTTPException

from app.providers.mock_a import MockProviderA
from app.providers.mock_b import MockProviderB
from app.schemas import ChatRequest, ChatResponse


class ProviderRouter:
    def __init__(self) -> None:
        self.providers = {"mock_a": MockProviderA(), "mock_b": MockProviderB()}

    async def chat(self, request: ChatRequest) -> ChatResponse:
        # Mock A is the default primary provider.
        if request.provider == "mock_b":
            primary_name = "Mock B"
            primary_provider = self.providers["mock_b"]
            fallback_name = "Mock A"
            fallback_provider = self.providers["mock_a"]
        else:
            primary_name = "Mock A"
            primary_provider = self.providers["mock_a"]
            fallback_name = "Mock B"
            fallback_provider = self.providers["mock_b"]

        print(f"Primary provider selected: {primary_name}")

        try:
            return await primary_provider.chat(request)

        except HTTPException as primary_error:
            # The primary provider already used all of its retries.
            print(f"Primary {primary_name} failed: {primary_error.detail}")

            # A client error is not retryable, so it should not trigger fallback.
            if primary_error.status_code < 500:
                print("Primary client error received. Not switching to fallback.")
                raise

            print(f"Switching to fallback: {fallback_name}")

            try:
                response = await fallback_provider.chat(request)
                print(f"Fallback {fallback_name} succeeded")
                return response

            except HTTPException as fallback_error:
                print(f"Fallback {fallback_name} failed: {fallback_error.detail}")
                raise HTTPException(
                    status_code=502,
                    detail="Both the primary and fallback providers failed.",
                )
