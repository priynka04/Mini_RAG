"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.models.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    """
    # Startup
    logger.info("🚀 Starting RAG application...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Vector DB: {settings.qdrant_url}")
    logger.info(f"Collection: {settings.qdrant_collection_name}")
    
    # TODO: Initialize Qdrant connection here in future steps
    # TODO: Verify OpenAI API key
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down RAG application...")


# Create FastAPI app
app = FastAPI(
    title="RAG Application API",
    description="Retrieval-Augmented Generation with multi-turn chat and citations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    # Basic health check
    # In future steps, we'll add actual connection checks
    return HealthResponse(
        status="healthy",
        qdrant_connected=False,  # Will implement in next step
        openai_configured=bool(settings.google_api_key),  # Using Gemini instead
        cohere_configured=bool(settings.cohere_api_key)
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAG Application API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ============================================================================
# IMPORT ROUTES
# ============================================================================

from app.routes import documents, chat
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )