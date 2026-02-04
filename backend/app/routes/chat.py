"""
API routes for chat and query handling.
"""
from fastapi import APIRouter, HTTPException
import logging
import time

# Add these imports for the reset endpoint
from qdrant_client import QdrantClient, models

from app.models.schemas import QueryRequest, QueryResponse, TimingInfo
from app.services.retrieval import get_retrieval_service
from app.services.llm import get_llm_service
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

"""
Simplified reset endpoint that avoids Pydantic validation errors.
Replace your current /reset endpoint in app/routes/chat.py with this.

This version skips the get_collection() call that's causing the Pydantic error.
"""
@router.post("/reset")
async def reset_vector_database():
    """
    Clear all vectors from the existing Qdrant collection.
    Safe for Qdrant Cloud. Does NOT recreate the collection.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter
        from app.config import settings

        # Optional safety guard
        if settings.environment != "development":
            raise HTTPException(
                status_code=403,
                detail="Vector reset is disabled outside development environment"
            )

        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )

        collection_name = settings.qdrant_collection_name

        # 🔥 THIS is the key line — delete ALL points safely
        result = client.delete(
            collection_name=collection_name,
            points_selector=Filter()  # empty filter = delete all
        )

        return {
            "status": "success",
            "message": "Vector database cleared",
            "operation_id": result.operation_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset Qdrant Cloud database: {str(e)}"
        )

# Alternative: Debug endpoint that ALSO skips get_collection()
@router.get("/debug/qdrant-simple")
async def debug_qdrant_simple():
    """
    Simplified debug endpoint that avoids get_collection() call.
    """
    try:
        if not settings.qdrant_api_key:
            return {"error": "QDRANT_API_KEY not configured"}
        
        qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=60,
            prefer_grpc=False
        )
        
        # Only list collections (this works fine)
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        return {
            "qdrant_url": settings.qdrant_url,
            "target_collection": settings.qdrant_collection_name,
            "target_exists": settings.qdrant_collection_name in collection_names,
            "all_collections": collection_names,
            "connection_status": "connected",
            "cloud": True,
            "api_key_set": True
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "connection_status": "failed"
        }
        
@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a user query with RAG pipeline.
    
    Pipeline:
    1. Retrieve relevant chunks (vector search)
    2. Rerank chunks (Cohere)
    3. Check relevance threshold
    4. Generate answer with citations (Gemini)
    
    Args:
        request: Query request with query text and optional chat history
        
    Returns:
        Query response with answer, sources, and metadata
    """
    overall_start = time.time()
    
    try:
        logger.info(f"Processing query: '{request.query[:50]}...'")
        
        # Step 1 & 2: Retrieve and rerank
        retrieval_service = get_retrieval_service()
        
        reranked_chunks, retrieval_timing = retrieval_service.retrieve_and_rerank(
            query=request.query
        )
        
        # Step 3: Check if we have relevant context
        has_relevant_context = retrieval_service.check_context_relevance(reranked_chunks)
        
        llm_service = get_llm_service()
        
        if not has_relevant_context:
            # No relevant context found
            logger.warning("No relevant context found - generating general answer")
            
            # Generate general knowledge answer
            general_answer, llm_timing = llm_service.generate_general_answer(request.query)
            
            total_time = (time.time() - overall_start) * 1000
            
            timing = TimingInfo(
                retrieval_ms=retrieval_timing.get('retrieval_ms', 0),
                rerank_ms=retrieval_timing.get('rerank_ms', 0),
                llm_ms=llm_timing.get('llm_ms', 0),
                total_ms=total_time
            )
            
            return QueryResponse(
                answer="I don't have information about this in the uploaded documents.",
                sources=[],
                has_context=False,
                general_answer=general_answer,
                timing=timing,
                token_usage=None,
                session_id=request.session_id
            )
        
        # Step 4: Generate answer with citations
        answer, sources, llm_timing, token_usage = llm_service.generate_answer(
            query=request.query,
            context_chunks=reranked_chunks,
            chat_history=request.chat_history
        )
        
        # Calculate total time
        total_time = (time.time() - overall_start) * 1000
        
        timing = TimingInfo(
            retrieval_ms=retrieval_timing.get('retrieval_ms', 0),
            rerank_ms=retrieval_timing.get('rerank_ms', 0),
            llm_ms=llm_timing.get('llm_ms', 0),
            total_ms=total_time
        )
        
        logger.info(f"✓ Query complete: {total_time:.0f}ms total")
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            has_context=True,
            timing=timing,
            token_usage=token_usage,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))