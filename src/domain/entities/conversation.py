from dataclasses import dataclass, field
from typing import List
import uuid
from datetime import datetime

@dataclass
class MessageEntity:
    role: str
    content: str
    conversation_id: uuid.UUID
    message_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ConversationEntity:
    user_id: uuid.UUID
    title: str = "New Conversation"
    conversation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    messages: List[MessageEntity] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
