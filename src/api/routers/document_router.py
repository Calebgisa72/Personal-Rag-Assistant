import uuid
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query

from api.dependencies import get_document_service, get_current_user
from services.document_service import DocumentService
from api.schemas.document_schemas import (
    DocumentUploadResponse,
    DocumentMetadataSchema,
    URLIngestionRequest,
    URLIngestionResponse,
    DocumentListResponse,
)

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type"),
    upload_status: Optional[str] = Query(None, description="Filter by upload status"),
    search_query: Optional[str] = Query(None, description="Search by title"),
    sort_by: str = Query(
        "created_at",
        description="Field to sort by (created_at, file_size_bytes, title)",
    ),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    document_service: DocumentService = Depends(get_document_service),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    documents, total = await document_service.list_documents(
        user_id=current_user_id,
        page=page,
        limit=limit,
        mime_type=mime_type,
        upload_status=upload_status,
        search_query=search_query,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    metadata_list = []
    for doc in documents:
        metadata_list.append(
            DocumentMetadataSchema(
                document_id=doc.document_id,
                title=doc.title,
                mime_type=doc.mime_type,
                size_bytes=doc.file_size_bytes,
                source="url" if not doc.file_path else "local_upload",
                chunk_count=doc.total_chunks,
                created_at=doc.created_at,
                custom_metadata=doc.metadata,
            )
        )

    return DocumentListResponse(documents=metadata_list, total=total)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    try:
        document = await document_service.upload_document(current_user_id, file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileExistsError as e:
        existing_doc = e.args[1]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(e),
                "existing_document_id": str(existing_doc.document_id),
                "existing_document_title": existing_doc.title,
                "created_at": existing_doc.created_at.isoformat(),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file locally or save metadata.",
        )

    metadata_schema = DocumentMetadataSchema(
        document_id=document.document_id,
        title=document.title,
        mime_type=document.mime_type,
        size_bytes=document.file_size_bytes,
        source="local_upload",
        created_at=document.created_at,
    )

    return DocumentUploadResponse(
        message="Document uploaded successfully", document=metadata_schema
    )


@router.post("/url", response_model=URLIngestionResponse)
async def ingest_url(
    request: URLIngestionRequest,
    document_service: DocumentService = Depends(get_document_service),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    try:
        await document_service.ingest_url(current_user_id, request.url)
    except FileExistsError as e:
        existing_doc = e.args[1]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(e),
                "existing_document_id": str(existing_doc.document_id),
                "existing_document_title": existing_doc.title,
                "created_at": existing_doc.created_at.isoformat(),
            },
        )
    except Exception as e:
        return URLIngestionResponse(
            message="Failed to scrape URL",
            documents_ingested=0,
            failed_urls=[request.url],
        )

    return URLIngestionResponse(
        message="URL ingested successfully", documents_ingested=1, failed_urls=[]
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    document_service: DocumentService = Depends(get_document_service),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    try:
        deleted = await document_service.delete_document(current_user_id, document_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
            )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not own this document",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document.",
        )

    return None
