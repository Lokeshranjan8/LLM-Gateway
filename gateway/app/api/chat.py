"""The HTTP door into the gateway."""

from fastapi import APIRouter

from app.router.router import ProviderRouter
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])
provider_router = ProviderRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    print(f"Request received: provider={request.provider}")
    response = await provider_router.chat(request)
    print(f"Returning response: provider={response.provider}")
    return response
