from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

@dataclass
class DocumentChunk:
    content: str
    document_id: uuid.UUID
    chunk_index: int
    metadata: Dict[str, Any]
    chunk_id: uuid.UUID = field(default_factory=uuid.uuid4)
    page_number: Optional[int] = None
    source: Optional[str] = None

@dataclass
class DocumentEntity:
    title: str
    content: str
    mime_type: str
    document_id: uuid.UUID = field(default_factory=uuid.uuid4)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class MessageEntity:
    role: str
    content: str
    message_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ConversationEntity:
    user_id: uuid.UUID
    conversation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    messages: List[MessageEntity] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)