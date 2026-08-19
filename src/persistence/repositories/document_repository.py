import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.interfaces import IDocumentRepository
from domain.entities import DocumentEntity
from infrastructure.database.models import DocumentMetadata

class DocumentRepository(IDocumentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, document: DocumentEntity) -> DocumentEntity:
        db_doc = DocumentMetadata(
            document_id=document.document_id,
            user_id=document.user_id,
            title=document.title,
            mime_type=document.mime_type,
            original_file_name=document.original_file_name,
            file_path=document.file_path,
            file_size_bytes=document.file_size_bytes,
            total_chunks=document.total_chunks,
            upload_status=document.upload_status,
            content_hash=document.content_hash,
            metadata_fields=document.metadata
        )
        self.session.add(db_doc)
        await self.session.flush()
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Optional[DocumentEntity]:
        stmt = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
        result = await self.session.execute(stmt)
        db_doc = result.scalar_one_or_none()
        if not db_doc:
            return None
        
        return DocumentEntity(
            document_id=db_doc.document_id,
            user_id=db_doc.user_id,
            title=db_doc.title,
            mime_type=db_doc.mime_type,
            original_file_name=db_doc.original_file_name,
            file_path=db_doc.file_path,
            file_size_bytes=db_doc.file_size_bytes,
            total_chunks=db_doc.total_chunks,
            upload_status=db_doc.upload_status,
            content_hash=db_doc.content_hash,
            metadata=db_doc.metadata_fields,
            created_at=db_doc.created_at,
            updated_at=db_doc.updated_at
        )

    async def get_by_user_id(self, user_id: uuid.UUID) -> List[DocumentEntity]:
        stmt = select(DocumentMetadata).where(DocumentMetadata.user_id == user_id).order_by(DocumentMetadata.created_at.desc())
        result = await self.session.execute(stmt)
        db_docs = result.scalars().all()
        
        return [
            DocumentEntity(
                document_id=d.document_id,
                user_id=d.user_id,
                title=d.title,
                mime_type=d.mime_type,
                original_file_name=d.original_file_name,
                file_path=d.file_path,
                file_size_bytes=d.file_size_bytes,
                total_chunks=d.total_chunks,
                upload_status=d.upload_status,
                content_hash=d.content_hash,
                metadata=d.metadata_fields,
                created_at=d.created_at,
                updated_at=d.updated_at
            ) for d in db_docs
        ]

    async def get_by_hash(self, user_id: uuid.UUID, content_hash: str) -> Optional[DocumentEntity]:
        stmt = select(DocumentMetadata).where(
            DocumentMetadata.user_id == user_id,
            DocumentMetadata.content_hash == content_hash
        )
        result = await self.session.execute(stmt)
        db_doc = result.scalar_one_or_none()
        if not db_doc:
            return None
        
        return DocumentEntity(
            document_id=db_doc.document_id,
            user_id=db_doc.user_id,
            title=db_doc.title,
            mime_type=db_doc.mime_type,
            original_file_name=db_doc.original_file_name,
            file_path=db_doc.file_path,
            file_size_bytes=db_doc.file_size_bytes,
            total_chunks=db_doc.total_chunks,
            upload_status=db_doc.upload_status,
            content_hash=db_doc.content_hash,
            metadata=db_doc.metadata_fields,
            created_at=db_doc.created_at,
            updated_at=db_doc.updated_at
        )

    async def update_status(self, document_id: uuid.UUID, status: str) -> bool:
        stmt = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
        result = await self.session.execute(stmt)
        db_doc = result.scalar_one_or_none()
        if not db_doc:
            return False
        
        db_doc.upload_status = status
        await self.session.flush()
        return True

    async def delete(self, document_id: uuid.UUID) -> bool:
        stmt = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
        result = await self.session.execute(stmt)
        db_doc = result.scalar_one_or_none()
        if not db_doc:
            return False
        
        await self.session.delete(db_doc)
        await self.session.flush()
        return True
