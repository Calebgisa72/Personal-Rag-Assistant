import uuid
import hashlib
from typing import List, Tuple, Optional
from fastapi import UploadFile

from persistence.uow import UnitOfWork
from services.storage_service import StorageService
from services.url_scraper_service import URLScraperService
from domain.entities import DocumentEntity
from infrastructure.vector_store.chroma_adapter import ChromaDBVectorStore
from infrastructure.document.parsers.parser_factory import ParserFactory
from infrastructure.document.chunking import SemanticChunkingService
from services.embedding_service import EmbeddingStrategyService
from infrastructure.ai.amali_provider import AmaliProvider
from core.config import settings
from core.logger import logger


class DocumentService:
    def __init__(
        self,
        uow: UnitOfWork,
        storage_service: StorageService,
        url_scraper_service: URLScraperService,
        vector_store: ChromaDBVectorStore,
    ):
        self.uow = uow
        self.storage_service = storage_service
        self.url_scraper_service = url_scraper_service
        self.vector_store = vector_store

    async def list_documents(
        self,
        user_id: uuid.UUID,
        page: int,
        limit: int,
        mime_type: Optional[str] = None,
        upload_status: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[DocumentEntity], int]:

        valid_sort_fields = ["created_at", "file_size_bytes", "title"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"

        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "desc"

        skip = (page - 1) * limit

        return await self.uow.documents.get_all_by_user_id_paginated(
            user_id=user_id,
            skip=skip,
            limit=limit,
            mime_type=mime_type,
            upload_status=upload_status,
            search_query=search_query,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def upload_document(
        self, user_id: uuid.UUID, file: UploadFile
    ) -> DocumentEntity:
        from services.ingestion_tasks import (
            process_and_ingest_document,
        )  # Import inside to avoid circular deps

        # Validate MIME type
        if file.content_type not in settings.ALLOWED_MIME_TYPES:
            raise ValueError(f"MIME type {file.content_type} not allowed.")

        # Save file to local storage
        try:
            file_path, file_size, file_hash = await self.storage_service.save_file(
                file, max_size=settings.MAX_UPLOAD_SIZE
            )
        except Exception as e:
            logger.error(f"StorageService failed: {e}")
            raise e

        # Check for conflicts
        existing_doc = await self.uow.documents.get_by_hash(user_id, file_hash)
        if existing_doc:
            self.storage_service.delete_file(file_path)
            raise FileExistsError(
                f"A document with this identical content already exists", existing_doc
            )

        # Create entity
        document = DocumentEntity(
            title=file.filename or "Untitled",
            mime_type=file.content_type,
            original_file_name=file.filename or "Unknown",
            file_path=file_path,
            file_size_bytes=file_size,
            user_id=user_id,
            upload_status="pending",
            content_hash=file_hash,
        )

        try:
            await self.uow.documents.create(document)
        except Exception as e:
            self.storage_service.delete_file(file_path)
            logger.error(f"Failed to save document metadata: {e}")
            raise RuntimeError("Failed to save document metadata.")

        # Trigger background ingestion task via Celery
        process_and_ingest_document.delay(str(document.document_id))
        return document

    async def ingest_url(self, user_id: uuid.UUID, url: str) -> DocumentEntity:
        from services.ingestion_tasks import (
            process_and_ingest_document,
        )  # Import inside to avoid circular deps

        try:
            title, text = await self.url_scraper_service.scrape(url)
        except Exception as e:
            logger.error(f"Failed to scrape URL {url}: {e}")
            raise RuntimeError(f"Failed to scrape URL {url}")

        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        existing_doc = await self.uow.documents.get_by_hash(user_id, text_hash)
        if existing_doc:
            raise FileExistsError(
                f"A document with this identical content already exists", existing_doc
            )

        file_size = len(text.encode("utf-8"))

        document = DocumentEntity(
            title=title,
            mime_type="text/html",
            original_file_name=url,
            file_path="",
            file_size_bytes=file_size,
            user_id=user_id,
            upload_status="pending",
            content_hash=text_hash,
            content=text,
        )

        try:
            await self.uow.documents.create(document)
        except Exception as e:
            logger.error(f"Failed to save URL document metadata: {e}")
            raise RuntimeError("Failed to save document metadata.")

        process_and_ingest_document.delay(str(document.document_id))
        return document

    async def delete_document(self, user_id: uuid.UUID, document_id: uuid.UUID) -> bool:
        document = await self.uow.documents.get_by_id(document_id)
        if not document:
            return False

        if document.user_id != user_id:
            raise PermissionError("User does not own this document")

        # 1. Delete from PostgreSQL
        deleted = await self.uow.documents.delete(document_id)
        if not deleted:
            logger.error(f"Failed to delete document {document_id} from PostgreSQL")
            raise RuntimeError("Failed to delete document from database.")

        # 2. Delete local file
        if document.file_path:
            file_deleted = self.storage_service.delete_file(document.file_path)
            if not file_deleted:
                logger.warning(
                    f"Could not delete local file for document {document_id} at {document.file_path}"
                )

        # 3. Delete from Vector Store
        try:
            await self.vector_store.delete_by_document_id(str(document_id))
        except Exception as e:
            logger.error(
                f"Failed to delete document {document_id} from vector store: {e}"
            )

        return True

    async def process_document_for_ingestion(self, document_id: uuid.UUID) -> None:
        """
        The core ingestion logic called by the background worker.
        """
        ai_provider = AmaliProvider()
        embedding_service = EmbeddingStrategyService(ai_provider=ai_provider)
        chunking_service = SemanticChunkingService()

        document = await self.uow.documents.get_by_id(document_id)
        if not document:
            logger.error(f"Document {document_id} not found in DB.")
            return

        try:
            # 1. Parsing
            if not document.content and document.file_path:
                parser = ParserFactory.get_parser(document.mime_type)
                document.content = parser.parse(document.file_path)

            if not document.content:
                raise ValueError("Document has no content after parsing.")

            # 2. Chunking
            chunks = chunking_service.chunk_document(document)

            if not chunks:
                document.upload_status = "completed"
                await self.uow.commit()
                return

            # 3. Embedding
            texts = [chunk.content for chunk in chunks]
            embeddings = await embedding_service.get_embeddings_batch(texts)

            # 4. Vector Store Insertion
            await self.vector_store.upsert(chunks, embeddings)

            # 5. Mark as completed
            document.upload_status = "completed"
            await self.uow.commit()

        except Exception as e:
            logger.error(f"Failed to ingest document {document_id}: {e}")
            document.upload_status = "failed"
            await self.uow.commit()
            raise e
