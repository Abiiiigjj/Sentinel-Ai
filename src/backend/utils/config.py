"""
Configuration settings for SentinelAI Backend
Uses pydantic-settings for environment variable management
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Ollama Configuration
    OLLAMA_HOST: str = "http://host.docker.internal:11434"
    LLM_MODEL: str = "mistral-nemo:12b-instruct-2407-q4_K_M"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # Data Storage
    DATA_DIR: Path = Path("./data")
    VECTOR_STORE_DIR: Path = Path("./data/vectorstore")
    DOCUMENTS_DIR: Path = Path("./data/documents")
    AUDIT_LOG_DIR: Path = Path("./data/audit")
    
    # PII Detection
    PII_DETECTION_ENABLED: bool = True
    PII_MASK_PATTERN: str = "[REDACTED]"
    SPACY_MODEL: str = "de_core_news_lg"  # German language model
    
    # Document Processing
    CHUNK_SIZE: int = 500  # Characters per chunk
    CHUNK_OVERLAP: int = 50  # Overlap between chunks
    MAX_DOCUMENT_SIZE_MB: int = 50
    
    # OCR Configuration (Phase 3)
    OCR_ENABLED: bool = True
    OCR_LANGUAGES: str = "deu+eng"  # Tesseract language codes
    OCR_MIN_TEXT_THRESHOLD: int = 50  # Min chars/page to consider non-scanned
    
    # Security
    ENCRYPTION_ENABLED: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        self.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        self.AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
