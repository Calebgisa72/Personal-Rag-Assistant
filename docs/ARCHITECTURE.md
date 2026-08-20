# Architecture Overview

This platform implements a **Clean Architecture** (Domain-Driven Design) to ensure high cohesion, low coupling, and maximum testability. 

## Layered Design

1. **API Layer (`src/api`)**: The presentation layer using FastAPI. Responsible for HTTP routing, request/response validation, API versioning, authentication dependencies, and middleware integration. It knows nothing about database models.
2. **Application / Service Layer (`src/services`)**: Business logic orchestration. The RAG pipeline (`RAGService`), semantic chunking workflow (`ChunkingService`), and embedding optimization (`EmbeddingStrategyService`) live here.
3. **Domain Layer (`src/domain`)**: Contains core entities and interfaces. Defines data structures (e.g., `DocumentEntity`, `DocumentChunk`) and contracts for repositories, vector stores, and AI providers.
4. **Infrastructure Layer (`src/infrastructure`)**: Concrete adapters for the outside world. This is where `AmaliAIProvider` (via `httpx`), `ChromaDBVectorStore`, and `RedisClient` reside.
5. **Persistence Layer (`src/persistence`)**: Handles the database schema and queries. Uses SQLAlchemy 2.x async, the Repository pattern, and Unit of Work to manage transaction boundaries.
6. **Core Layer (`src/core`)**: Cross-cutting concerns such as configuration (`Pydantic BaseSettings`), structured logging (`structlog`), exceptions, and middleware.

## Architectural Invariants (World-Class Standards)
To maintain a senior-level codebase, the following invariants MUST be strictly followed:
1. **No Business Logic in Routers**: The API Layer (`routers`) must never contain business logic, such as data manipulation, validation of domain concepts, direct file system interactions, or calling repositories directly. Routers should strictly parse requests, delegate to the Service Layer, and map responses.
2. **Dependency Injection**: All dependencies (services, repositories, config) must be injected via FastAPI's `Depends` or passed through constructors. No direct instantiation of classes inside function logic or global scopes.
3. **Thin Background Workers**: Celery tasks (or any background workers) should act as thin wrappers that instantiate or receive an Application Service and invoke a method on it. Do not duplicate service layer logic or dependency orchestration inside a background worker file.

## Scalability and Maintainability
* **Separation of Concerns**: Because external providers are abstracted via interfaces in the Domain layer, swapping ChromaDB for Pinecone or Amali AI for another LLM provider requires zero changes to the business logic.
* **Concurrency**: Using `httpx.AsyncClient` alongside asynchronous data fetching (Postgres + Redis) prevents I/O blocking. The custom Amali AI embedding provider specifically implements concurrent gathering (`asyncio.gather`) for single-string embedding constraints, enabling parallel batch processing.
* **Cost Efficiency**: Dedicated `CostService` and robust `EmbeddingStrategyService` lay the groundwork for cache-hit optimization to avoid redundant AI queries.

## Production Readiness Checklist

Before taking this to production, ensure the following are completed:
- [ ] **Security**: Implement JWT authentication, input sanitization, file upload limits, and secure secret management via Vault/KMS.
- [ ] **Testing**: Write comprehensive unit tests for domain logic and integration tests for external dependencies. Achieve >80% code coverage.
- [ ] **CI/CD**: Configure GitHub Actions (or similar) for linting, dependency scanning, testing, and deployment.
- [ ] **Monitoring**: Add OpenTelemetry tracing and expose Prometheus metrics. Monitor rate limits and external provider API latencies.
- [ ] **Caching & Rate Limiting**: Implement a Redis-backed Token Bucket algorithm for per-user rate limiting and semantic caching for duplicate queries.
- [ ] **Backups**: Configure automated backups for Postgres and ChromaDB storage volumes.
- [ ] **Disaster Recovery**: Define an RTO/RPO policy and test data restoration.
