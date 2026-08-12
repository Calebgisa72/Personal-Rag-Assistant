# Functional Requirements

This document outlines the core functional capabilities of the RAG SaaS platform.

## 1. Document Ingestion and Processing
- **Multi-format Support**: System must support parsing of PDFs, DOCX, TXT, CSV, HTML, and Markdown files.
- **Chunking Engine**: Uses `LangChain`'s `RecursiveCharacterTextSplitter`. Must preserve metadata (source, page number, document ID). Configurable overlap and chunk sizes.
- **Embedding Generation**: Utilizes `HuggingFaceEmbeddings` with `sentence-transformers/all-MiniLM-L6-v2`. Must support concurrent generation to bypass single-string provider limitations.

## 2. Knowledge Retrieval (RAG)
- **Vector Storage**: Must index chunks into a vector database (ChromaDB default, extensible to Pinecone/Qdrant).
- **Semantic Search**: Must retrieve top-K most relevant chunks based on cosine similarity of user queries.
- **Context Assembly**: The `RAGService` must assemble retrieved chunks into a coherent system prompt for the AI Provider.
- **Hybrid Search**: (Future) Must combine semantic search with BM25 keyword search.

## 3. Conversation & Memory
- **Memory Tracking**: Must maintain user conversation histories, allowing contextual follow-up questions.
- **Session Management**: Must isolate conversation context per user to ensure data privacy.

## 4. Usage and Cost Analytics
- **Token Tracking**: Must calculate input/output token usage for every interaction.
- **Cost Estimation**: Must map token usage to provider pricing models (e.g., `Amali AI / GPT-4o-mini`).
- **Reporting**: Must provide aggregated usage reports per user and globally.

## 5. Caching and Performance
- **Semantic Caching**: Must use Redis to cache embeddings and generated answers for repeated questions.
- **Rate Limiting**: Must implement Redis-backed token-bucket rate limiting per IP and per user.
