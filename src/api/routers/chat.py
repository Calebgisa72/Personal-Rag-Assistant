from fastapi import APIRouter, Depends, BackgroundTasks
import uuid
from api.dependencies import get_rag_service, get_current_user
from services.rag_service import RAGService
from api.schemas.chat_schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    rag_service: RAGService = Depends(get_rag_service),
    current_user: uuid.UUID = Depends(get_current_user),
):
    answer, conv_id, needs_summarization = await rag_service.ask_question(
        question=request.question,
        user_id=current_user,
        conversation_id_str=request.conversation_id,
    )

    if needs_summarization:
        # Trigger the summarization in the background
        background_tasks.add_task(rag_service.summarize_conversation, conv_id)

    return ChatResponse(answer=answer, conversation_id=conv_id)
