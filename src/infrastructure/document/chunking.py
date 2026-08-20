from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from domain.entities import DocumentEntity, DocumentChunk
from core.config import settings
import uuid


class SemanticChunkingService:
    def __init__(self):
        # Fallback/standard splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # Markdown header splitters for documents parsed with structure
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )

    def chunk_document(self, document: DocumentEntity) -> List[DocumentChunk]:
        """
        Chunks a document semantically. For Markdown-like text (or text structured with headers),
        it uses MarkdownHeaderTextSplitter. Otherwise, falls back to RecursiveCharacterTextSplitter.
        """
        # A simple heuristic: if the text contains markdown headers, use markdown splitter
        # This can be expanded based on the output of specific parsers
        chunks = []
        if "# " in document.content or "## " in document.content:
            md_splits = self.markdown_splitter.split_text(document.content)
            total_chunks = len(md_splits)
            # If the splits are still too large, we could run them through the RecursiveCharacterTextSplitter
            # But for simplicity, we treat the semantic splits as chunks.
            for index, doc in enumerate(md_splits):
                # Langchain Document object has 'page_content' and 'metadata'
                combined_metadata = {
                    "title": document.title,
                    "mime_type": document.mime_type,
                    **document.metadata,
                    **doc.metadata,  # Includes header info
                }

                chunk = DocumentChunk(
                    chunk_id=uuid.uuid4(),
                    content=doc.page_content,
                    document_id=document.document_id,
                    chunk_index=index,
                    total_chunks=total_chunks,
                    metadata=combined_metadata,
                    source=document.metadata.get("source", "unknown"),
                    page_number=document.metadata.get("page_number", None),
                )
                chunks.append(chunk)
        else:
            # Fallback to recursive splitting
            texts = self.text_splitter.split_text(document.content)
            total_chunks = len(texts)
            for index, text in enumerate(texts):
                chunk = DocumentChunk(
                    chunk_id=uuid.uuid4(),
                    content=text,
                    document_id=document.document_id,
                    chunk_index=index,
                    total_chunks=total_chunks,
                    metadata={
                        "title": document.title,
                        "mime_type": document.mime_type,
                        **document.metadata,
                    },
                    source=document.metadata.get("source", "unknown"),
                    page_number=document.metadata.get("page_number", None),
                )
                chunks.append(chunk)

        return chunks
