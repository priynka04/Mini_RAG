"""
Google Gemini embeddings service for generating vector representations of text.
"""
from typing import List
import logging
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using Google Gemini API.
    Uses text-embedding-004 model (768 dimensions).
    """
    
    def __init__(self):
        """Initialize Gemini client."""
        genai.configure(api_key=settings.google_api_key)
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension
        
        logger.info(f"Initialized EmbeddingService with model: {self.model}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Clean text
            text = text.replace("\n", " ").strip()
            
            if not text:
                raise ValueError("Cannot embed empty text")
            
            # Call Gemini API
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )
            
            embedding = result['embedding']
            
            # Verify dimension
            if len(embedding) != self.dimension:
                logger.warning(
                    f"Expected dimension {self.dimension}, got {len(embedding)}"
                )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Gemini API supports batch embedding, but we'll process one at a time
        for better error handling with free tier rate limits.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        all_embeddings = []
        
        for i, text in enumerate(texts):
            try:
                # Clean text
                cleaned_text = text.replace("\n", " ").strip()
                
                if not cleaned_text:
                    logger.warning(f"Skipping empty text at index {i}")
                    continue
                
                # Call Gemini API
                result = genai.embed_content(
                    model=self.model,
                    content=cleaned_text,
                    task_type="retrieval_document"
                )
                
                embedding = result['embedding']
                all_embeddings.append(embedding)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Generated {i + 1}/{len(texts)} embeddings")
                
            except Exception as e:
                logger.error(f"Error embedding text {i}: {e}")
                raise
        
        logger.info(f"Total embeddings generated: {len(all_embeddings)}")
        return all_embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Uses task_type="retrieval_query" for queries.
        
        Args:
            query: Search query text
            
        Returns:
            Query embedding vector
        """
        try:
            query = query.replace("\n", " ").strip()
            
            if not query:
                raise ValueError("Cannot embed empty query")
            
            # Use retrieval_query task type for queries
            result = genai.embed_content(
                model=self.model,
                content=query,
                task_type="retrieval_query"
            )
            
            return result['embedding']
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise


# Global instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create the global EmbeddingService instance.
    
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service