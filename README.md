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

### Prerequisites
- Python 3.12+
- PostgreSQL
- Redis
- (Optional) ChromaDB (Local persist directory is used by default)

### 1. Installation
Clone the repository and install the dependencies:
```bash
python -m venv venv
# On Windows use: venv\Scripts\activate
# On Linux/macOS use: source venv/bin/activate
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the sample environment file and configure it:
```bash
cp .env.example .env
```
Update the `.env` file with your PostgreSQL, Redis, and Amali AI Provider credentials. For example:
```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db
REDIS_URL=redis://localhost:6379/0
CHROMA_PERSIST_DIRECTORY=./chroma_data
AMALI_API_URL=https://ai-api.amalitech.org/api/v2/public/v1
AMALI_API_KEY=your_amali_api_key_here
```

### 3. Database Migrations
Make sure your PostgreSQL server is running and the database specified in `DATABASE_URL` (e.g., `rag_db`) is created. Then, apply the migrations using Alembic:
```bash
alembic upgrade head
```

### 4. Running the Application
Start the FastAPI server using Uvicorn. Since the app is in the `src` folder, you might need to specify the Python path on Windows, or just run Uvicorn directly if installed in the virtual environment:
```bash
# On Windows (PowerShell):
$env:PYTHONPATH="src"
uvicorn src.api.main:app --reload

# On Linux/macOS:
PYTHONPATH=src uvicorn src.api.main:app --reload
```

The API will be available at `http://localhost:8000`.
You can view the interactive API documentation at `http://localhost:8000/docs`.
