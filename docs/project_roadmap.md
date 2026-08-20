# Personal RAG Assistant - Project Roadmap

This roadmap outlines the chronological development plan to elevate the Personal RAG Assistant to a production-ready, highly professional standard. Tasks are grouped logically by the branches they should be developed on.

## Core Architectural Standards
To ensure this remains a senior-level, world-class project, all branches MUST adhere to:
1. **Clean Architecture**: API Routers must **never** contain business logic. All logic must be pushed down to Application Services (e.g., `DocumentService`).
2. **Dependency Injection**: Use FastAPI `Depends()` for all service and repository instantiation. No global instances.
3. **Decoupled Background Tasks**: Celery workers must be thin wrappers that inject an Application Service and call its methods.

---

## Branch: `feature/01-database-modeling`
**Goal:** Establish the foundation for persistent storage of metadata, users, and conversations using SQLAlchemy (PostgreSQL).

- [ ] **SQLAlchemy Setup:** Configure `src/persistence/database.py` with SQLAlchemy async engine and session maker.
- [ ] **Model Implementation:** Translate `src/domain/entities.py` dataclasses to SQLAlchemy declarative base models (`User`, `Conversation`, `Message`, `DocumentMetadata`).
  - *Note:* Do NOT save document content in Postgres. Postgres should only store metadata and relationships. Document chunks should also be embedded and we save the embedded vectors in ChromaDB for symantic search and retrieval.
- [ ] **Alembic Migrations:** Setup Alembic for database schema versioning. Create the initial migration script.
- [ ] **Repository Pattern Update:** Implement the SQLAlchemy repositories for `ConversationRepository` and `DocumentRepository` in `src/persistence/`.

---

## Branch: `feature/02-document-ingestion-pipeline`
**Goal:** Implement a robust file uploading and URL scraping pipeline to ingest various formats.

- [ ] **Local File Storage:** Implement a storage service (`src/services/storage_service.py`) to save uploaded files (`.pdf`, `.docx`, `.txt`, `.csv`) to an `uploads/` directory with unique IDs.
- [ ] **Upload API Endpoint:** Create `POST /api/v1/documents/upload` in a new `document_router`.
- [ ] **File Validation:** Add middleware/dependency validation for file size limits (e.g., max 10MB) and MIME type checking before saving.
- [ ] **URL Ingestion Strategy:** Create `POST /api/v1/documents/url` to scrape content from web links (using libraries like `BeautifulSoup` or `playwright`).
- [ ] **Document Metadata Tracking:** Upon successful upload/scrape, save the metadata (size, title, source, MIME type) using the SQLAlchemy models.

---

## Branch: `feature/03-advanced-parsing-and-chunking`
**Goal:** Extract text effectively from complex files and intelligently chunk them for optimal vector search.

- [ ] **Format Parsers:** Implement strategy pattern for parsing different MIME types in `src/infrastructure/document/parsers/`:
  - `PDFParser` (using `PyMuPDF` or `pdfplumber` to handle tables/images).
  - `CSVParser` (row-based context embedding).
  - `DocxParser`.
- [ ] **Semantic Chunking:** Upgrade `src/infrastructure/document/chunking.py` from basic `RecursiveCharacterTextSplitter` to semantic chunking (e.g., chunking by header markdown, preserving logical sections).
- [ ] **Vector Store Pipeline:** Wire the output of the chunker directly to the embedding service and save the chunks into ChromaDB/Pinecone.

---

## Branch: `feature/04-document-retrieval-api`
**Goal:** Allow users to manage their knowledge base via the API.

- [ ] **List Documents API:** Create `GET /api/v1/documents` to fetch the user's uploaded documents (paginated), returning the `DocumentListResponse` schema.
- [ ] **Delete Document API:** Create `DELETE /api/v1/documents/{id}` to remove the file from local storage, delete metadata from Postgres, and remove associated chunks from the Vector Store.

---

## Branch: `feature/05-conversational-memory-and-context`
**Goal:** Implement a senior-level RAG context strategy that includes conversational memory and smart summarization.

- [ ] **Save Chat History:** Update `ChatRequest` to accept a `conversation_id`. If provided, fetch past messages from Postgres. Save the new user question and AI answer to the DB.
- [ ] **History Summarization Strategy:**
  - Implement a background task or inline check: if `len(messages) >= 15` in a conversation, trigger the LLM to generate a compressed summary of the older messages.
  - Save this summary to a new `ConversationSummary` table/column.
- [ ] **Context Composition Logic:** Update `src/services/rag_service.py` to construct the prompt powerfully:
  - Provide the **Conversation Summary** at the top of the prompt.
  - Append the **last 10 messages** verbatim for immediate context.
  - Inject the **Top-K Vector Store Chunks** based on the current user query.
  - Append the **Current User Prompt**.
- [ ] **Prompt Engineering:** Refine the system prompt to instruct the AI on how to weigh the conversational memory vs. the factual retrieved chunks.

---

## Branch: `feature/06-auth-and-security`
**Goal:** Secure the API and isolate user data.

- [ ] **JWT Authentication:** Add OAuth2 with JWT tokens. Create `POST /api/v1/auth/login`.
- [ ] **User Context:** Inject the current `user_id` into all API endpoints using FastAPI `Depends`.
- [ ] **Data Isolation:** Ensure Vector Store queries use metadata filtering (`filter={"user_id": current_user.id}`) so users can only RAG over their own documents.

---

## Branch: `feature/07-production-readiness`
**Goal:** Prepare the application for deployment.

- [ ] **Dockerization:** Create `Dockerfile` and `docker-compose.yml` (including PostgreSQL and ChromaDB services).
- [ ] **CI/CD Pipeline:** Setup GitHub Actions for linting (Ruff/Black) and basic unit testing (Pytest).
- [ ] **Logging & Monitoring:** Integrate structured JSON logging and potentially an APM like DataDog or Sentry.
