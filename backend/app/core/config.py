import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "AI Document QA"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # OpenAI Settings
    OPENAI_API_KEY: str
    MODEL_NAME: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Storage Settings
    UPLOAD_DIR: str = "data/uploads"
    VECTOR_STORE_DIR: str = "data/vector_store"
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 4

    # Security Settings
    SECRET_KEY: str = "super_secret_dev_key_change_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./sql_app.db"

    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Pinecone Settings
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = "document-qa"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Ensure directories exist
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/vector_store", exist_ok=True)

settings = Settings()
