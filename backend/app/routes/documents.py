"""
API routes for document upload and management.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import logging

from app.models.schemas import TextProcessRequest, DocumentUploadResponse
from app.services.ingestion import get_ingestion_service
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """
    Upload and process a document (PDF, TXT, or Markdown).
    
    Args:
        file: Document file
        title: Optional custom title
        
    Returns:
        Document upload response with statistics
    """
    try:
        # Validate file type
        file_extension = file.filename.split('.')[-1].lower()
        if f".{file_extension}" not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: .{file_extension}. "
                       f"Allowed: {', '.join(settings.allowed_file_types)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.max_file_size_mb}MB"
            )
        
        # Process document
        ingestion_service = get_ingestion_service()
        
        result = ingestion_service.ingest_uploaded_file(
            file_content=content,
            filename=file.filename,
            title=title
        )
        
        return DocumentUploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text", response_model=DocumentUploadResponse)
async def process_text(request: TextProcessRequest):
    """
    Process pasted text directly.
    
    Args:
        request: Text content and optional title
        
    Returns:
        Document upload response with statistics
    """
    try:
        ingestion_service = get_ingestion_service()
        
        result = ingestion_service.ingest_text(
            text=request.text,
            title=request.title or "Pasted Text"
        )
        
        return DocumentUploadResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """
    Get statistics about ingested documents.
    
    Returns:
        Statistics about the vector store
    """
    try:
        ingestion_service = get_ingestion_service()
        stats = ingestion_service.get_ingestion_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))