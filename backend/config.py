"""
LexiVault AI - Configuration Management
Centralizada como en consulta-smart e idp-smart
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración global de LexiVault AI"""

    # ========================================================================
    # APP CONFIGURATION
    # ========================================================================
    APP_NAME: str = os.getenv("APP_NAME", "LexiVault AI")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_ENV: str = os.getenv("APP_ENV", "production")
    DEBUG: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")

    # ========================================================================
    # DATABASE CONFIGURATION (PostgreSQL + pgvector)
    # ========================================================================
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "casmarts-core-db-primary")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "casmarts_secure_pwd")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "lexivault")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # ========================================================================
    # JWT & AUTHENTICATION
    # ========================================================================
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production-very-long-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # ========================================================================
    # SECURITY & ENCRYPTION
    # ========================================================================
    SYSTEM_MASTER_KEY: Optional[str] = os.getenv("SYSTEM_MASTER_KEY")
    DOCUMENT_ENCRYPTION_KEY: Optional[str] = os.getenv("DOCUMENT_ENCRYPTION_KEY")

    # ========================================================================
    # STORAGE (MinIO / Ceph)
    # ========================================================================
    CEPH_ENDPOINT_URL: str = os.getenv("CEPH_ENDPOINT_URL", "http://casmarts-core-storage:8333")
    CEPH_ACCESS_KEY: str = os.getenv("CEPH_ACCESS_KEY", "admin")
    CEPH_SECRET_KEY: str = os.getenv("CEPH_SECRET_KEY", "casmarts_secure_pwd")
    CEPH_BUCKET_NAME: str = os.getenv("CEPH_BUCKET_NAME", "lexivault")

    # ========================================================================
    # CACHE & MESSAGE BROKER (Valkey)
    # ========================================================================
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://casmarts-core-cache:6379/4")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://casmarts-core-cache:6379/4")

    # ========================================================================
    # MESSAGE STREAMING (Redpanda / Kafka)
    # ========================================================================
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "casmarts-core-redpanda:29092")
    ENABLE_KAFKA: bool = os.getenv("ENABLE_KAFKA", "false").lower() == "true"
    KAFKA_TOPIC_FILE_UPLOADED: str = os.getenv("KAFKA_TOPIC_FILE_UPLOADED", "lexivault.documents.uploaded")

    # ========================================================================
    # GOOGLE CLOUD / VERTEX AI (DEFAULT LLM)
    # ========================================================================
    GCP_PROJECT_ID: Optional[str] = os.getenv("GCP_PROJECT_ID", "project-9a4f42ad-5486-49f3-83b")
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
    GCP_CREDENTIALS_JSON: Optional[str] = os.getenv(
        "GCP_CREDENTIALS_JSON",
        "/app/google-v-credentials.json"
    )
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    VERTEX_MODEL: str = os.getenv("VERTEX_MODEL", "gemini-1.5-pro")
    
    # Alias para compatibilidad con genai SDK
    @property
    def GEMINI_MODEL(self) -> str:
        return self.VERTEX_MODEL

    # ========================================================================
    # LLM CONFIGURATION (Multi-provider support, Vertex AI primary)
    # ========================================================================
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "vertex")  # vertex, google, groq, nvidia
    
    # Google API (Gemini)
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")

    # NVIDIA NIM
    NVIDIA_NIM_API_KEY: Optional[str] = os.getenv("NVIDIA_NIM_API_KEY")
    NVIDIA_NIM_BASE_URL: str = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_NIM_MODEL: str = os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.3-70b-instruct")

    # Groq
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # ========================================================================
    # DOCUMENT PROCESSING (Docling abstraction layer)
    # ========================================================================
    # Currently using Vertex AI (multimodal), ready to migrate to Docling
    DOCLING_PROVIDER: str = os.getenv("DOCLING_PROVIDER", "vertex")  # vertex or docling
    DOCLING_SERVER_URL: Optional[str] = os.getenv("DOCLING_SERVER_URL", "http://casmarts-core-docling:5000/extract")

    # Document parsing settings
    MAX_DOCUMENT_SIZE_MB: int = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "100"))
    SUPPORTED_FORMATS: list = ["pdf", "docx", "xlsx", "pptx", "png", "jpg", "jpeg", "tiff"]
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "4000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "500"))

    # ========================================================================
    # EMBEDDINGS (Local with Ollama or remote)
    # ========================================================================
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "vertex")  # vertex or ollama
    OLLAMA_API_BASE_URL: str = os.getenv("OLLAMA_API_BASE_URL", "http://ollama:11434")
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "768"))

    # ========================================================================
    # VAULT (HashiCorp - for secrets management)
    # ========================================================================
    VAULT_ADDR: Optional[str] = os.getenv("VAULT_ADDR")
    VAULT_DEV_ROOT_TOKEN_ID: Optional[str] = os.getenv("VAULT_DEV_ROOT_TOKEN_ID")

    # ========================================================================
    # SECURITY SCANNING
    # ========================================================================
    CLAMAV_HOST: str = os.getenv("CLAMAV_HOST", "lexivault-clamav")
    CLAMAV_PORT: int = int(os.getenv("CLAMAV_PORT", "3310"))
    ENABLE_ANTIVIRUS_SCAN: bool = os.getenv("ENABLE_ANTIVIRUS_SCAN", "true").lower() == "true"

    # ========================================================================
    # RAG & SEMANTIC SEARCH
    # ========================================================================
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
