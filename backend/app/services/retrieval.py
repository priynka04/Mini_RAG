"""
Retrieval and reranking service.
Pipeline: Query → Vector Search → Rerank → Return Top Results
"""
import time
from typing import List, Tuple
import logging
import cohere

from app.config import settings
from app.services.embeddings import get_embedding_service
from app.services.vectorstore import get_vectorstore_service
from app.models.schemas import RetrievedChunk, RerankedChunk

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service for retrieving and reranking relevant chunks.
    
    Pipeline:
    1. Embed query
    2. Vector search (top-k retrieval)
    3. Rerank results (Cohere)
    4. Return top results
    """
    
    def __init__(self):
        """Initialize retrieval service."""
        self.embedding_service = get_embedding_service()
        self.vectorstore = get_vectorstore_service()
        
        # Initialize Cohere reranker
        self.cohere_client = cohere.Client(settings.cohere_api_key)
        
        logger.info("RetrievalService initialized with Cohere reranker")
    
    def retrieve_and_rerank(
        self,
        query: str,
        top_k_retrieval: int = None,
        top_k_rerank: int = None
    ) -> Tuple[List[RerankedChunk], dict]:
        """
        Retrieve relevant chunks and rerank them.
        
        Args:
            query: User query
            top_k_retrieval: Number of chunks to retrieve (default from settings)
            top_k_rerank: Number of chunks to return after reranking (default from settings)
            
        Returns:
            Tuple of (reranked_chunks, timing_info)
        """
        # Use defaults from settings if not provided
        if top_k_retrieval is None:
            top_k_retrieval = settings.top_k_retrieval
        if top_k_rerank is None:
            top_k_rerank = settings.top_k_rerank
        
        timing = {}
        
        # Step 1: Embed query
        start_time = time.time()
        logger.info(f"Embedding query: '{query[:50]}...'")
        query_embedding = self.embedding_service.embed_query(query)
        timing['embedding_ms'] = (time.time() - start_time) * 1000
        
        # Step 2: Vector search
        start_time = time.time()
        logger.info(f"Retrieving top {top_k_retrieval} chunks from vector store")
        retrieved_chunks = self.vectorstore.search(
            query_embedding=query_embedding,
            top_k=top_k_retrieval,
            score_threshold=None  # No threshold for initial retrieval
        )
        timing['retrieval_ms'] = (time.time() - start_time) * 1000
        
        if not retrieved_chunks:
            logger.warning("No chunks retrieved from vector store")
            return [], timing
        
        logger.info(f"Retrieved {len(retrieved_chunks)} chunks")
        
        # Step 3: Rerank using Cohere
        start_time = time.time()
        logger.info(f"Reranking with Cohere (top {top_k_rerank})")
        
        reranked_chunks = self._rerank_with_cohere(
            query=query,
            chunks=retrieved_chunks,
            top_k=top_k_rerank
        )
        
        timing['rerank_ms'] = (time.time() - start_time) * 1000
        
        logger.info(
            f"✓ Retrieval complete: {len(reranked_chunks)} chunks "
            f"(retrieval: {timing['retrieval_ms']:.0f}ms, "
            f"rerank: {timing['rerank_ms']:.0f}ms)"
        )
        
        return reranked_chunks, timing
    
    def _rerank_with_cohere(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int
    ) -> List[RerankedChunk]:
        """
        Rerank chunks using Cohere Rerank API.
        
        Args:
            query: User query
            chunks: Retrieved chunks
            top_k: Number of top results to return
            
        Returns:
            List of reranked chunks
        """
        try:
            # Prepare documents for reranking
            documents = [chunk.text for chunk in chunks]
            
            # Call Cohere Rerank API
            rerank_response = self.cohere_client.rerank(
                query=query,
                documents=documents,
                top_n=top_k,
                model="rerank-english-v3.0"  # or rerank-multilingual-v3.0
            )
            
            # Convert to RerankedChunk objects
            reranked_chunks = []
            
            for result in rerank_response.results:
                original_chunk = chunks[result.index]
                
                reranked_chunk = RerankedChunk(
                    chunk_id=original_chunk.chunk_id,
                    text=original_chunk.text,
                    score=result.relevance_score,  # Cohere rerank score
                    original_score=original_chunk.score,  # Original vector score
                    metadata=original_chunk.metadata
                )
                
                reranked_chunks.append(reranked_chunk)
            
            logger.info(
                f"Reranked {len(reranked_chunks)} chunks "
                f"(scores: {[f'{c.score:.3f}' for c in reranked_chunks[:3]]})"
            )
            
            return reranked_chunks
            
        except Exception as e:
            logger.error(f"Error reranking with Cohere: {e}")
            # Fallback: return original chunks without reranking
            logger.warning("Falling back to vector search results without reranking")
            return [
                RerankedChunk(
                    chunk_id=c.chunk_id,
                    text=c.text,
                    score=c.score,
                    original_score=c.score,
                    metadata=c.metadata
                )
                for c in chunks[:top_k]
            ]
    
    def check_context_relevance(
        self,
        reranked_chunks: List[RerankedChunk]
    ) -> bool:
        """
        Check if the reranked chunks are relevant enough to answer the query.
        
        Uses the minimum rerank score threshold from settings.
        
        Args:
            reranked_chunks: Reranked chunks
            
        Returns:
            True if context is relevant enough
        """
        if not reranked_chunks:
            return False
        
        # Check if top result meets minimum threshold
        top_score = reranked_chunks[0].score
        
        is_relevant = top_score >= settings.min_rerank_score
        
        logger.info(
            f"Context relevance check: top_score={top_score:.3f}, "
            f"threshold={settings.min_rerank_score}, relevant={is_relevant}"
        )
        
        return is_relevant


# Global instance
_retrieval_service = None


def get_retrieval_service() -> RetrievalService:
    """
    Get or create the global RetrievalService instance.
    
    Returns:
        RetrievalService instance
    """
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service