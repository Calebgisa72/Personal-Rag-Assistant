# RAG SaaS Platform

This is the foundation for an enterprise AI-powered Retrieval-Augmented Generation (RAG) SaaS platform.

## Key Features
- **Clean Architecture**: Domain-Driven Design principles with clear separation of concerns (API, Domain, Services, Infrastructure, Persistence).
- **Asynchronous Stack**: `FastAPI`, `SQLAlchemy 2.x` (Async), `asyncpg`.
- **RAG Capabilities**: Configurable LangChain document chunking, HuggingFace embeddings (`all-MiniLM-L6-v2`), and ChromaDB vector indexing.
- **AI Integrations**: Integrated with a custom AI Provider (Amali AI) via an OpenAI-compatible API utilizing `httpx.AsyncClient`.
- **Observability**: Request tracing and structured logging using `structlog`.
- **Performance**: Ready for Redis caching, rate limiting, and batch concurrent embeddings.
- **Cost Tracking**: Built-in architecture for token and usage cost estimations.

## Setup Instructions

See the `ARCHITECTURE.md`, `API_REFERENCE.md`, and `FUNCTIONAL_REQUIREMENTS.md` documents for detailed insights into the design.

### Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
