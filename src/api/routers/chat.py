from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api.dependencies import get_rag_service
from src.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    question: str
    conversation_id: str = None

class ChatResponse(BaseModel):
    answer: str

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    answer = await rag_service.ask_question(request.question)
    return ChatResponse(answer=answer)\n