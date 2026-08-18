import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List

from api.dependencies import get_uow, get_vector_store
from persistence.uow import UnitOfWork
from infrastructure.vector_store.chroma_adapter import ChromaDBVectorStore
from services.storage_service import StorageService
from services.url_scraper_service import URLScraperService
from domain.entities import DocumentEntity
from api.schemas.document_schemas import (
    DocumentUploadResponse,
    DocumentMetadataSchema,
    URLIngestionRequest,
    URLIngestionResponse
)
from core.config import settings
from core.logger import logger

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
storage_service = StorageService()
url_scraper_service = URLScraperService()

# Hardcoded user ID for now since Auth is not implemented
DUMMY_USER_ID = uuid.UUID(int=1)

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    uow: UnitOfWork = Depends(get_uow)
):
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type {file.content_type} not allowed."
        )

    # Save file to local storage
    try:
        file_path, file_size = await storage_service.save_file(file, max_size=settings.MAX_UPLOAD_SIZE)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file locally."
        )
    document = DocumentEntity(
        title=file.filename or "Untitled",
        mime_type=file.content_type,
        original_file_name=file.filename or "Unknown",
        file_path=file_path,
        file_size_bytes=file_size,
        user_id=DUMMY_USER_ID,
        upload_status="pending"
    )

    try:
        await uow.documents.create(document)
    except Exception as e:
        storage_service.delete_file(file_path)
        logger.error(f"Failed to save document metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document metadata."
        )

    metadata_schema = DocumentMetadataSchema(
        document_id=document.document_id,
        title=document.title,
        mime_type=document.mime_type,
        size_bytes=document.file_size_bytes,
        source="local_upload",
        created_at=document.created_at
    )
    
    return DocumentUploadResponse(
        message="Document uploaded successfully",
        document=metadata_schema
    )

@router.post("/url", response_model=URLIngestionResponse)
async def ingest_url(
    request: URLIngestionRequest,
    uow: UnitOfWork = Depends(get_uow)
):
    try:
        title, text = await url_scraper_service.scrape(request.url)
    except Exception as e:
        return URLIngestionResponse(
            message="Failed to scrape URL",
            documents_ingested=0,
            failed_urls=[request.url]
        )

    file_size = len(text.encode('utf-8'))
    
    document = DocumentEntity(
        title=title,
        mime_type="text/html",
        original_file_name=request.url,
        file_path="", 
        file_size_bytes=file_size,
        user_id=DUMMY_USER_ID,
        upload_status="pending",
        content=text 
    )

    try:
        await uow.documents.create(document)
    except Exception as e:
        logger.error(f"Failed to save document metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document metadata."
        )

    return URLIngestionResponse(
        message="URL ingested successfully",
        documents_ingested=1,
        failed_urls=[]
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_uow),
    vector_store: ChromaDBVectorStore = Depends(get_vector_store)
):
    document = await uow.documents.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
    
    # 1. Delete from PostgreSQL
    deleted = await uow.documents.delete(document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document from database."
        )

    # 2. Delete local file
    if document.file_path:
        storage_service.delete_file(document.file_path)

    # 3. Delete from Vector Store
    try:
        await vector_store.delete_by_document_id(str(document_id))
    except Exception as e:
        logger.error(f"Failed to delete document from vector store: {e}")
        # Not throwing an error here so the user isn't stuck with a ghost entry in DB
        
    return None
