from fastapi import APIRouter, Depends
from api.dependencies import get_rag_service
from services.rag_service import RAGService
from api.schemas.chat_schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    answer = await rag_service.ask_question(request.question)
    return ChatResponse(answer=answer)
