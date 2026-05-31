from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.models.schemas import ChatRequest, ChatResponse
from app.rag.pipeline import RagPipeline

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, user_id: UUID = Depends(get_current_user_id)) -> ChatResponse:
    return await RagPipeline().answer_question(user_id=user_id, payload=payload)
