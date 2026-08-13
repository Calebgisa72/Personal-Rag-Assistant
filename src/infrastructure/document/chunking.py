from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any, Optional
from domain.entities import DocumentEntity, DocumentChunk
from core.config import settings

class ChunkingService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_document(self, document: DocumentEntity) -> List[DocumentChunk]:
        # Using LangChain to split
        texts = self.text_splitter.split_text(document.content)
        
        chunks = []
        for index, text in enumerate(texts):
            chunk = DocumentChunk(
                content=text,
                document_id=document.document_id,
                chunk_index=index,
                metadata={
                    "title": document.title,
                    "mime_type": document.mime_type,
                    **document.metadata
                },
                source=document.metadata.get("source", "unknown"),
                page_number=document.metadata.get("page_number", None)
            )
            chunks.append(chunk)
        return chunks