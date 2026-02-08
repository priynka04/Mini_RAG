"""
Gemini Embeddings Service (v1beta compatible)
Uses gemini-embedding-001 (3072 dimensions)
"""

from typing import List
import logging
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        genai.configure(api_key=settings.google_api_key)

        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension

        logger.info(
            f"Initialized Gemini EmbeddingService with model: {self.model}"
        )

    def _clean(self, text: str) -> str:
        return text.replace("\n", " ").strip()

    def embed_text(self, text: str) -> List[float]:
        text = self._clean(text)
        if not text:
            raise ValueError("Cannot embed empty text")

        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document",
        )

        embedding = result["embedding"]

        if len(embedding) != self.dimension:
            logger.warning(
                f"Embedding dimension mismatch: "
                f"expected {self.dimension}, got {len(embedding)}"
            )

        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []

        for i, text in enumerate(texts):
            cleaned = self._clean(text)
            if not cleaned:
                logger.warning(f"Skipping empty chunk at index {i}")
                continue

            try:
                result = genai.embed_content(
                    model=self.model,
                    content=cleaned,
                    task_type="retrieval_document",
                )
                embeddings.append(result["embedding"])

            except Exception as e:
                logger.error(f"Embedding failed at index {i}: {e}")
                raise

        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        query = self._clean(query)
        if not query:
            raise ValueError("Cannot embed empty query")

        result = genai.embed_content(
            model=self.model,
            content=query,
            task_type="retrieval_query",
        )

        return result["embedding"]


_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
