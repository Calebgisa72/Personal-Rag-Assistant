from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import uuid
from datetime import datetime


@dataclass
class DocumentChunk:
    content: str
    document_id: uuid.UUID
    chunk_index: int
    metadata: Dict[str, Any]
    chunk_id: uuid.UUID = field(default_factory=uuid.uuid4)
    total_chunks: Optional[int] = None
    page_number: Optional[int] = None
    source: Optional[str] = None


@dataclass
class DocumentEntity:
    title: str
    mime_type: str
    original_file_name: str
    file_path: str  # e.g., 'uploads/uuid-filename.pdf'
    file_size_bytes: int
    user_id: uuid.UUID
    total_chunks: Optional[int] = None
    upload_status: str = "pending"  # pending, processed, failed
    document_id: uuid.UUID = field(default_factory=uuid.uuid4)
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: Optional[str] = None
    content: Optional[str] = None  # Kept for in-memory extraction passing, not for DB
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
