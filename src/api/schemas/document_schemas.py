from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class DocumentMetadataSchema(BaseModel):
    document_id: uuid.UUID
    title: str
    mime_type: str
    size_bytes: Optional[int] = None
    source: Optional[str] = None
    chunk_count: Optional[int] = None
    created_at: datetime
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentMetadataSchema

class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadataSchema]
    total: int

class URLIngestionRequest(BaseModel):
    url: str = Field(..., description="The URL to scrape and ingest")
    max_depth: Optional[int] = Field(1, description="Crawling depth")

class URLIngestionResponse(BaseModel):
    message: str
    documents_ingested: int
    failed_urls: List[str] = Field(default_factory=list)

class DuplicateDocumentError(BaseModel):
    message: str
    existing_document_id: uuid.UUID
    existing_document_title: str
    created_at: datetime
