"""The HTTP door into the gateway."""

from fastapi import APIRouter, HTTPException, Request, Response

from app.config import settings
from app.rate_limit.token_bucket import TokenBucket
from app.router.router import ProviderRouter
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])
provider_router = ProviderRouter()
token_bucket = TokenBucket()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    http_request: Request,
    http_response: Response,
) -> ChatResponse:
    # There is no authentication yet, so use the client IP as the bucket ID.
    client_id = http_request.client.host if http_request.client else "unknown"
    limit = token_bucket.check_rate_limit(client_id)

    if not limit["allowed"]:
        print(f"Rate limit exceeded for {client_id}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "Retry-After": str(limit["retry_after"]),
                "X-RateLimit-Limit": str(settings.token_bucket_capacity),
                "X-RateLimit-Remaining": "0",
            },
        )

    http_response.headers["X-RateLimit-Limit"] = str(settings.token_bucket_capacity)
    http_response.headers["X-RateLimit-Remaining"] = str(limit["remaining_tokens"])

    print(f"Request received: provider={chat_request.provider}")
    response = await provider_router.chat(chat_request)
    print(f"Returning response: provider={response.provider}")
    return response
