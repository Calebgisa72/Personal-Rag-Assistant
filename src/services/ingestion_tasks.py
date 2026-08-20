import asyncio
import uuid
from core.celery_app import celery_app
from core.logger import logger
from persistence.uow import UnitOfWork
from persistence.database import SessionLocal
from infrastructure.vector_store.chroma_adapter import ChromaDBVectorStore
from services.storage_service import StorageService
from services.url_scraper_service import URLScraperService

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@celery_app.task(bind=True)
def process_and_ingest_document(self, document_id_str: str):
    """
    Background task to parse, chunk, embed, and store a document in the vector store.
    """
    logger.info(f"Starting ingestion for document {document_id_str}")
    document_id = uuid.UUID(document_id_str)
    
    async def _ingest():
        from services.document_service import DocumentService
        
        # Setup dependencies for the service layer
        uow = UnitOfWork()
        vector_store = ChromaDBVectorStore()
        storage_service = StorageService()
        url_scraper_service = URLScraperService()
        
        document_service = DocumentService(
            uow=uow,
            storage_service=storage_service,
            url_scraper_service=url_scraper_service,
            vector_store=vector_store
        )
        
        async with uow:
            await document_service.process_document_for_ingestion(document_id)
            logger.info(f"Successfully finished ingestion task for {document_id_str}")

    # Run the async ingestion workflow
    try:
        run_async(_ingest())
    except Exception as e:
        logger.error(f"Task failed for document {document_id_str}: {e}")
        raise e
