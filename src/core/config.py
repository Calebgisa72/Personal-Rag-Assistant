from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG SaaS Platform"
    VERSION: str = "0.1.0"

    # Environment
    ENV: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db"

    # Redis Cache & Rate Limiting
    REDIS_URL: str = "redis://localhost:6379/0"

    # Vector Store
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"

    # AI Provider (Amali AI)
    AMALI_API_URL: str = "https://ai-api.amalitech.org/api/v2/public/v1"
    AMALI_API_KEY: str = "dummy_key"
    AMALI_PROVIDER_NAME: str = "openai"  # or anthropic
    
    # Generation config
    RAG_TEMPERATURE: float = 0.0
    CHAT_TEMPERATURE: float = 0.7
    INSUFFICIENT_CONTEXT_TEMPERATURE: float = 0.1
    RAG_RELEVANCE_THRESHOLD: float = 0.35

    # Embedding config
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"

    # Chunking config
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_MIME_TYPES: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/csv",
    ]

    # Conversational Memory
    MAX_MESSAGES_BEFORE_SUMMARY: int = 15
    MESSAGES_TO_KEEP_AFTER_SUMMARY: int = 10

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
