"""Gateway adapter for Groq's chat-completions API."""

from fastapi import HTTPException
import requests

from app.config import settings
from app.providers.base import BaseProvider
from app.schemas import ChatRequest, ChatResponse

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_RETRIES = 2


class GroqProvider(BaseProvider):
    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not settings.groq_api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.groq_model,
            "messages": [{"role": "user", "content": request.message}],
        }

        for attempt in range(1, MAX_RETRIES + 2):
            print(f"Calling Groq (attempt {attempt})...")

            try:
                response = requests.post(
                    GROQ_CHAT_URL,
                    headers=headers,
                    json=payload,
                    timeout=20,
                )

                if 200 <= response.status_code < 300:
                    data = response.json()
                    message = data["choices"][0]["message"]["content"]
                    print(f"Groq attempt {attempt} succeeded")
                    return ChatResponse(provider="groq", message=message)

                if response.status_code >= 500 and attempt <= MAX_RETRIES:
                    print(f"Groq attempt {attempt} failed: HTTP {response.status_code}")
                    print("Retrying Groq...")
                    continue

                if response.status_code >= 500:
                    raise HTTPException(
                        status_code=502,
                        detail="Groq failed after all retry attempts.",
                    )

                raise HTTPException(
                    status_code=response.status_code,
                    detail="Groq rejected the request.",
                )

            except requests.exceptions.Timeout:
                if attempt <= MAX_RETRIES:
                    print(f"Groq attempt {attempt} timed out. Retrying...")
                    continue

                raise HTTPException(
                    status_code=504,
                    detail="Groq timed out after all retry attempts.",
                )

            except requests.exceptions.ConnectionError:
                if attempt <= MAX_RETRIES:
                    print(f"Groq attempt {attempt} could not connect. Retrying...")
                    continue

                raise HTTPException(
                    status_code=503,
                    detail="Unable to connect to Groq after all retry attempts.",
                )

            except HTTPException:
                raise

            except (KeyError, IndexError, ValueError) as error:
                print(f"Unexpected Groq response: {str(error)}")
                raise HTTPException(
                    status_code=502,
                    detail="Groq returned an unexpected response.",
                )
