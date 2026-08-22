from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class MessageAttachmentSchema(BaseModel):
    attachment_id: uuid.UUID
    file_name: str
    file_type: str
    is_temporary: bool

class MessageSchema(BaseModel):
    role: str = Field(
        ..., description="Role of the sender (e.g., 'user', 'assistant', 'system')"
    )
    content: str = Field(..., description="Content of the message")
    message_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    attachments: List[MessageAttachmentSchema] = Field(default_factory=list)


class RenameConversationRequest(BaseModel):
    title: str = Field(..., description="New title for the conversation")

class PinConversationRequest(BaseModel):
    is_pinned: bool = Field(..., description="Pin status")



class ChatRequest(BaseModel):
    question: str = Field(..., description="The user's input question")
    conversation_id: Optional[str] = Field(
        None, description="Optional ID of the conversation to maintain context"
    )


class ChatResponse(BaseModel):
    answer: str = Field(..., description="The generated answer from the RAG pipeline")
    conversation_id: Optional[str] = Field(
        None, description="The ID of the conversation"
    )


class ConversationSummarySchema(BaseModel):
    summary: str = Field(..., description="Compressed summary of past messages")
    message_count: int = Field(..., description="Number of messages summarized")
    last_summarized_at: datetime


class ConversationSchema(BaseModel):
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    messages: List[MessageSchema] = Field(default_factory=list)
    summary: Optional[ConversationSummarySchema] = None
    created_at: datetime
    updated_at: datetime
    is_pinned: bool

class ConversationListResponse(BaseModel):
    items: List[ConversationSchema]
    total: int
    limit: int
    offset: int
