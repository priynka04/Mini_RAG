"""
Document ingestion service - complete pipeline from upload to vector store.
"""
import time
from typing import Dict, Any, Tuple
import logging
from pathlib import Path
import tempfile
import os

from app.utils.parsers import DocumentParser
from app.utils.chunking import create_chunks_from_document
from app.utils.metadata import generate_chunk_id
from app.services.embeddings import get_embedding_service
from app.services.vectorstore import get_vectorstore_service
from app.config import settings

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service for ingesting documents into the RAG system.
    
    Pipeline:
    1. Parse document (extract text, links, images)
    2. Chunk text with metadata
    3. Generate embeddings
    4. Store in vector database
    """
    
    def __init__(self):
        """Initialize ingestion service."""
        self.embedding_service = get_embedding_service()
        self.vectorstore = get_vectorstore_service()
        
        # Ensure collection exists
        if not self.vectorstore.collection_exists():
            logger.info("Creating vector store collection...")
            self.vectorstore.create_collection()
        
        logger.info("IngestionService initialized")
    
    def ingest_text(
        self,
        text: str,
        title: str = "Pasted Text",
        source_name: str = None
    ) -> Dict[str, Any]:
        """
        Ingest pasted text directly.
        
        Args:
            text: Raw text content
            title: Document title
            source_name: Optional source identifier
            
        Returns:
            Ingestion result with statistics
        """
        start_time = time.time()
        
        try:
            # Generate source name if not provided
            if not source_name:
                source_name = f"text_{int(time.time())}.txt"
            
            logger.info(f"Ingesting text: {title} ({len(text)} chars)")
            
            # Parse text
            parsed = DocumentParser.parse_raw_text(text, title)
            
            # Delete existing chunks from this source (if any)
            self._delete_existing_source(source_name)
            
            # Chunk text
            chunks_with_metadata = create_chunks_from_document(
                text=parsed.text,
                source=source_name,
                title=parsed.title,
                links=parsed.links,
                images=parsed.images,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            
            # Extract chunks and metadata
            chunks = []
            metadatas = []
            
            for idx, (chunk_text, base_metadata) in enumerate(chunks_with_metadata):
                chunks.append(chunk_text)
                
                # Add unique chunk ID
                metadata = base_metadata.copy()
                metadata["chunk_id"] = generate_chunk_id(chunk_text, source_name, idx)
                metadatas.append(metadata)
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self.embedding_service.embed_batch(chunks)
            
            # Store in vector database
            logger.info("Storing in vector database...")
            count = self.vectorstore.upsert_chunks(chunks, embeddings, metadatas)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = {
                "success": True,
                "document_id": source_name,
                "title": title,
                "chunks_created": count,
                "links_extracted": len(parsed.links),
                "images_extracted": len(parsed.images),
                "processing_time_ms": processing_time
            }
            
            logger.info(f"✓ Text ingestion complete: {count} chunks in {processing_time:.0f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting text: {e}")
            raise
    
    def ingest_file(
        self,
        file_path: str,
        title: str = None
    ) -> Dict[str, Any]:
        """
        Ingest a document file (PDF, TXT, MD).
        
        Args:
            file_path: Path to the file
            title: Optional custom title (otherwise extracted from file)
            
        Returns:
            Ingestion result with statistics
        """
        start_time = time.time()
        
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_name = Path(file_path).name
            
            logger.info(f"Ingesting file: {file_name} ({file_size} bytes)")
            
            # Validate file type
            file_extension = Path(file_path).suffix.lower()
            if file_extension not in settings.allowed_file_types:
                raise ValueError(
                    f"Unsupported file type: {file_extension}. "
                    f"Allowed: {settings.allowed_file_types}"
                )
            
            # Validate file size
            if file_size > settings.max_file_size_bytes:
                raise ValueError(
                    f"File too large: {file_size} bytes. "
                    f"Max: {settings.max_file_size_bytes} bytes"
                )
            
            # Parse document
            logger.info("Parsing document...")
            parsed = DocumentParser.parse_file(file_path)
            
            # Use custom title if provided
            if title:
                parsed.title = title
            
            # Delete existing chunks from this source (if any)
            self._delete_existing_source(file_name)
            
            # Chunk text
            logger.info("Chunking text...")
            chunks_with_metadata = create_chunks_from_document(
                text=parsed.text,
                source=file_name,
                title=parsed.title,
                links=parsed.links,
                images=parsed.images,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            
            # Extract chunks and metadata
            chunks = []
            metadatas = []
            
            for idx, (chunk_text, base_metadata) in enumerate(chunks_with_metadata):
                chunks.append(chunk_text)
                
                # Add unique chunk ID
                metadata = base_metadata.copy()
                metadata["chunk_id"] = generate_chunk_id(chunk_text, file_name, idx)
                metadatas.append(metadata)
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self.embedding_service.embed_batch(chunks)
            
            # Store in vector database
            logger.info("Storing in vector database...")
            count = self.vectorstore.upsert_chunks(chunks, embeddings, metadatas)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = {
                "success": True,
                "document_id": file_name,
                "title": parsed.title,
                "chunks_created": count,
                "links_extracted": len(parsed.links),
                "images_extracted": len(parsed.images),
                "processing_time_ms": processing_time
            }
            
            logger.info(
                f"✓ File ingestion complete: {count} chunks in {processing_time:.0f}ms"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting file: {e}")
            raise
    
    def ingest_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        title: str = None
    ) -> Dict[str, Any]:
        """
        Ingest an uploaded file (from FastAPI UploadFile).
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            title: Optional custom title
            
        Returns:
            Ingestion result with statistics
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=Path(filename).suffix
            ) as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            try:
                # Process the file
                result = self.ingest_file(temp_path, title=title or filename)
                
                # Update document_id to use original filename
                result["document_id"] = filename
                
                return result
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"Error ingesting uploaded file: {e}")
            raise
    
    def _delete_existing_source(self, source_name: str):
        """
        Delete existing chunks from a source (implements delete + reinsert).
        
        Args:
            source_name: Source document name
        """
        try:
            existing_count = self.vectorstore.count_points()
            if existing_count > 0:
                logger.info(f"Deleting existing chunks from: {source_name}")
                self.vectorstore.delete_by_source(source_name)
        except Exception as e:
            logger.warning(f"Could not delete existing source: {e}")
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """
        Get statistics about ingested documents.
        
        Returns:
            Statistics dict
        """
        try:
            total_chunks = self.vectorstore.count_points()
            collection_info = self.vectorstore.get_collection_info()
            
            return {
                "total_chunks": total_chunks,
                "collection_name": collection_info.get("name", ""),
                "status": collection_info.get("status", ""),
                "vector_count": collection_info.get("vectors_count", 0)
            }
        except Exception as e:
            logger.error(f"Error getting ingestion stats: {e}")
            return {
                "total_chunks": 0,
                "error": str(e)
            }


# Global instance
_ingestion_service = None


def get_ingestion_service() -> IngestionService:
    """
    Get or create the global IngestionService instance.
    
    Returns:
        IngestionService instance
    """
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service