from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from domain.interfaces import IVectorStore
from domain.entities import DocumentChunk
from core.config import settings

class ChromaDBVectorStore(IVectorStore):
    def __init__(self, collection_name: str = "rag_collection"):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(name=collection_name)

    async def upsert(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        ids = [str(chunk.chunk_id) for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            # Flatten metadata to string/int/float for Chroma
            meta = chunk.metadata.copy()
            meta["document_id"] = str(chunk.document_id)
            meta["chunk_index"] = chunk.chunk_index
            if chunk.page_number is not None:
                meta["page_number"] = chunk.page_number
            if chunk.source:
                meta["source"] = chunk.source
            metadatas.append(meta)

        # Chroma doesn't natively support async yet, but we wrap it in a pseudo-async interface
        # for architectural consistency. Real implementations could offload this to a threadpool.
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    async def similarity_search(self, query_embedding: List[float], k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_dict
        )
        
        chunks = []
        if not results["ids"] or not results["ids"][0]:
            return chunks
            
        for i in range(len(results["ids"][0])):
            chunk_id_str = results["ids"][0][i]
            content = results["documents"][0][i]
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            
            import uuid
            chunk = DocumentChunk(
                chunk_id=uuid.UUID(chunk_id_str),
                content=content,
                document_id=uuid.UUID(meta.get("document_id", str(uuid.uuid4()))),
                chunk_index=meta.get("chunk_index", 0),
                page_number=meta.get("page_number"),
                source=meta.get("source"),
                metadata=meta
            )
            chunks.append(chunk)
            
        return chunks