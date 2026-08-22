from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from datetime import datetime


@dataclass
class MessageAttachmentEntity:
    file_name: str
    file_type: str
    is_temporary: bool
    parsed_content: Optional[str]
    message_id: uuid.UUID
    attachment_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class MessageEntity:
    role: str
    content: str
    conversation_id: uuid.UUID
    message_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    attachments: List[MessageAttachmentEntity] = field(default_factory=list)


@dataclass
class ConversationSummaryEntity:
    summary: str
    message_count: int
    last_summarized_at: datetime
    summary_id: uuid.UUID = field(default_factory=uuid.uuid4)
    conversation_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class ConversationEntity:
    user_id: uuid.UUID
    title: str = "New Conversation"
    conversation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    messages: List[MessageEntity] = field(default_factory=list)
    summary: Optional[ConversationSummaryEntity] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_pinned: bool = False
