"""
Application configuration using Pydantic Settings.
Loads from environment variables with validation.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google Gemini Configuration
    google_api_key: str
    
    # Qdrant Cloud Configuration
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection_name: str = "rag_docs"
    
    # Cohere Configuration (for reranking)
    cohere_api_key: str
    
    # Application Settings
    environment: str = "development"
    chunk_size: int = 1000
    chunk_overlap: int = 120
    top_k_retrieval: int = 15
    top_k_rerank: int = 5
    chat_history_turns: int = 3
    
    # LLM Settings
    llm_model: str = "gemini-1.5-flash"
    embedding_model: str = "models/text-embedding-004"
    embedding_dimension: int = 768  # Gemini embeddings are 768-dimensional
    
    # CORS Settings
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # Similarity thresholds
    min_similarity_score: float = 0.5  # Minimum vector similarity for relevance
    min_rerank_score: float = 0.3      # Minimum rerank score for context
    
    # File upload limits
    max_file_size_mb: int = 10
    allowed_file_types: List[str] = [".pdf", ".txt", ".md"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()