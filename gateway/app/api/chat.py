"""The HTTP door into the gateway."""

from fastapi import APIRouter

from app.router.router import ProviderRouter
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])
provider_router = ProviderRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # Pass the request to the router. The router chooses Mock A or Mock B.
    return await provider_router.chat(request)
