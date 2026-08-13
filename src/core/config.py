from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

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
    
    # Embedding config
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Chunking config
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()