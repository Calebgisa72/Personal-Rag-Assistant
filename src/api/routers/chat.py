from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    Form,
    File,
    UploadFile,
    HTTPException,
    status,
)
import uuid
from typing import Optional
from api.dependencies import get_rag_service, get_current_user, get_conversation_service
from services.rag_service import RAGService
from services.conversation_service import ConversationService
from api.schemas.chat_schemas import (
    ChatResponse,
    RenameConversationRequest,
    PinConversationRequest,
    ConversationSchema,
    ConversationListResponse,
)

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    background_tasks: BackgroundTasks,
    question: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    rag_service: RAGService = Depends(get_rag_service),
    current_user: uuid.UUID = Depends(get_current_user),
):
    answer, conv_id, needs_summarization = await rag_service.ask_question(
        question=question,
        user_id=current_user,
        conversation_id_str=conversation_id,
        file=file,
    )

    if needs_summarization:
        background_tasks.add_task(rag_service.summarize_conversation, conv_id)

    return ChatResponse(answer=answer, conversation_id=conv_id)


@router.patch("/conversations/{conversation_id}/title")
async def rename_conversation(
    conversation_id: uuid.UUID,
    request: RenameConversationRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: uuid.UUID = Depends(get_current_user),
):
    try:
        await conversation_service.rename_conversation(
            user_id=current_user, conversation_id=conversation_id, title=request.title
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rename conversation",
        )
    return {"message": "Conversation renamed successfully"}


@router.patch("/conversations/{conversation_id}/pin")
async def pin_conversation(
    conversation_id: uuid.UUID,
    request: PinConversationRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: uuid.UUID = Depends(get_current_user),
):
    try:
        await conversation_service.pin_conversation(
            user_id=current_user,
            conversation_id=conversation_id,
            is_pinned=request.is_pinned,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update pin status",
        )
    return {"message": "Conversation pin status updated successfully"}


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = 1,
    limit: int = 20,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: uuid.UUID = Depends(get_current_user),
):
    convs, total = await conversation_service.list_conversations(
        user_id=current_user, page=page, limit=limit
    )
    offset = (page - 1) * limit
    return ConversationListResponse(
        items=convs, total=total, limit=limit, offset=offset
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(
    conversation_id: uuid.UUID,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: uuid.UUID = Depends(get_current_user),
):
    try:
        conv = await conversation_service.get_conversation(
            user_id=current_user, conversation_id=conversation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation",
        )
    return conv
