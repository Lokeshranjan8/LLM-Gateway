from fastapi import HTTPException

from app.circuit_breaker import CircuitBreaker
from app.metrics import fallback_total
from app.config import settings
from app.providers.groq import GroqProvider
from app.providers.mock_a import MockProviderA
from app.providers.mock_b import MockProviderB
from app.schemas import ChatRequest, ChatResponse


class ProviderRouter:
    def __init__(self) -> None:
        self.providers = {
            "groq": GroqProvider(),
            "mock_a": MockProviderA(),
            "mock_b": MockProviderB(),
        }
        self.circuits = {
            "groq": CircuitBreaker(
                "Groq",
                settings.circuit_failure_threshold,
                settings.circuit_cooldown_seconds,
            ),
            "mock_a": CircuitBreaker(
                "Mock A",
                settings.circuit_failure_threshold,
                settings.circuit_cooldown_seconds,
            ),
            "mock_b": CircuitBreaker(
                "Mock B",
                settings.circuit_failure_threshold,
                settings.circuit_cooldown_seconds,
            ),
        }

    async def chat(self, request: ChatRequest) -> ChatResponse:
        # Groq is the default primary provider. Mock A stays available for testing.
        if request.provider == "mock_b":
            primary_key = "mock_b"
            primary_name = "Mock B"
            primary_provider = self.providers["mock_b"]
            fallback_name = "Groq"
            fallback_provider = self.providers["groq"]
        elif request.provider == "mock_a":
            primary_key = "mock_a"
            primary_name = "Mock A"
            primary_provider = self.providers["mock_a"]
            fallback_name = "Mock B"
            fallback_provider = self.providers["mock_b"]
        else:
            primary_key = "groq"
            primary_name = "Groq"
            primary_provider = self.providers["groq"]
            fallback_name = "Mock B"
            fallback_provider = self.providers["mock_b"]

        print(f"Primary provider selected: {primary_name}")
        circuit = self.circuits[primary_key]

        if not circuit.can_call_provider():
            return await self.call_fallback(fallback_name, fallback_provider, request)

        try:
            response = await primary_provider.chat(request)
            circuit.record_success()
            return response

        except HTTPException as primary_error:
            print(f"Primary {primary_name} failed: {primary_error.detail}")

            if primary_error.status_code < 500:
                print("Primary client error received. Not switching to fallback.")
                raise

            circuit.record_failure()
            return await self.call_fallback(fallback_name, fallback_provider, request)

    async def call_fallback(self,fallback_name: str,fallback_provider,request: ChatRequest,) -> ChatResponse:
        print(f"Switching to fallback: {fallback_name}")
        fallback_total.inc()

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
