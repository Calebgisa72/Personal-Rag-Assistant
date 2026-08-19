import asyncio
import uuid
from core.celery_app import celery_app
from core.logger import logger
from persistence.uow import UnitOfWork
from persistence.database import SessionLocal
from infrastructure.document.parsers.parser_factory import ParserFactory
from infrastructure.document.chunking import SemanticChunkingService
from infrastructure.vector_store.chroma_adapter import ChromaDBVectorStore
from services.embedding_service import EmbeddingStrategyService
from infrastructure.ai.amali_provider import AmaliProvider # Assuming this exists from original repo structure

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Since Celery is synchronous by default, we need a helper to run async code inside it
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
        # Setup dependencies
        # Assuming we can instantiate a UnitOfWork directly for background task
        # Normally this might require a slightly different setup if using FastAPI Depends
        uow = UnitOfWork(SessionLocal) 
        
        # We need the vector store and embedding service
        vector_store = ChromaDBVectorStore()
        ai_provider = AmaliProvider() # Instantiate the provider
        embedding_service = EmbeddingStrategyService(ai_provider=ai_provider)
        chunking_service = SemanticChunkingService()
        
        async with uow:
            document = await uow.documents.get_by_id(document_id)
            if not document:
                logger.error(f"Document {document_id_str} not found in DB.")
                return

            try:
                # 1. Parsing
                if not document.content and document.file_path:
                    # Parse local file
                    parser = ParserFactory.get_parser(document.mime_type)
                    document.content = parser.parse(document.file_path)
                    logger.info(f"Successfully parsed {document.file_path}")
                
                if not document.content:
                    raise ValueError("Document has no content after parsing.")
                
                # 2. Chunking
                chunks = chunking_service.chunk_document(document)
                logger.info(f"Generated {len(chunks)} chunks for {document_id_str}")
                
                if not chunks:
                    logger.warning("No chunks generated. Finishing task.")
                    document.upload_status = "completed"
                    await uow.commit()
                    return

                # 3. Embedding (batching might be needed for very large documents)
                texts = [chunk.content for chunk in chunks]
                embeddings = await embedding_service.get_embeddings_batch(texts)
                
                # 4. Vector Store Insertion
                await vector_store.upsert(chunks, embeddings)
                
                # 5. Mark as completed
                document.upload_status = "completed"
                await uow.commit()
                logger.info(f"Successfully ingested document {document_id_str}")
                
            except Exception as e:
                logger.error(f"Failed to ingest document {document_id_str}: {e}")
                document.upload_status = "failed"
                await uow.commit()
                raise e

    # Run the async ingestion workflow
    run_async(_ingest())
