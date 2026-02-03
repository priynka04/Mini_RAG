"""
Qdrant vector store service for storing and retrieving document embeddings.
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams,
    PayloadSchemaType
)

from app.config import settings
from app.models.schemas import ChunkMetadata, RetrievedChunk

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Service for interacting with Qdrant Cloud vector database.
    
    Handles:
    - Collection creation and management
    - Upserting document chunks with embeddings
    - Vector similarity search
    - Metadata filtering
    """
    
    def __init__(self):
        """Initialize Qdrant client."""
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        self.collection_name = "rag_doc"
        self.vector_size = settings.embedding_dimension
        
        logger.info(f"Initialized VectorStoreService: {settings.qdrant_url}")
        logger.info(f"Collection: {self.collection_name}")
    
    def create_collection(self, recreate: bool = False) -> bool:
        """
        Create Qdrant collection if it doesn't exist.
        """
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if exists:
                if recreate:
                    logger.info(f"Deleting existing collection: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"Collection '{self.collection_name}' already exists")
            else:    
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                ),
            )

        # ✅ CRITICAL: create payload index for filtering & deletion
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="source",
                    field_schema=PayloadSchemaType.KEYWORD,
             )
                logger.info("✓ Payload index created for 'source'")
            except Exception:
                logger.info("✓ Payload index for 'source' already exists")

            return True

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
        raise


    def collection_exists(self) -> bool:
        """
        Check if collection exists.
        
        Returns:
            True if collection exists
        """
        try:
            collections = self.client.get_collections().collections
            return any(c.name == self.collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection.
        
        Returns:
            Collection info dict
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def upsert_chunks(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> int:
        """
        Upsert document chunks with embeddings and metadata.
        
        Args:
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts
            
        Returns:
            Number of points upserted
        """
        if len(chunks) != len(embeddings) != len(metadatas):
            raise ValueError("Chunks, embeddings, and metadatas must have same length")
        
        if not chunks:
            return 0
        
        try:
            # Create points
            points = []
            for chunk, embedding, metadata in zip(chunks, embeddings, metadatas):
                # Generate unique ID
                point_id = str(uuid.uuid4())
                
                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk,
                        "chunk_id": metadata.get("chunk_id", ""),
                        "source": metadata.get("source", ""),
                        "title": metadata.get("title", ""),
                        "section": metadata.get("section", ""),
                        "links": metadata.get("links", []),
                        "images": metadata.get("images", []),
                        "created_at": datetime.utcnow().isoformat()
                    }
                )
                points.append(point)
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"✓ Upserted {len(points)} chunks to Qdrant")
            return len(points)
            
        except Exception as e:
            logger.error(f"Error upserting chunks: {e}")
            raise
    
    def delete_by_source(self, source: str) -> bool:
        """
        Delete all chunks from a specific source document.
        
        This implements the "delete + reinsert" strategy for document updates.
        
        Args:
            source: Source document name
            
        Returns:
            True if successful
        """
        try:
            # Delete points matching the source
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="source",
                            match=MatchValue(value=source)
                        )
                    ]
                )
            )
            
            logger.info(f"✓ Deleted chunks from source: {source}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting by source: {e}")
            raise
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 15,
        score_threshold: Optional[float] = None,
        filter_source: Optional[str] = None
    ) -> List[RetrievedChunk]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score (optional)
            filter_source: Filter by source document (optional)
            
        Returns:
            List of retrieved chunks with scores and metadata
        """
        try:
            # Build filter if needed
            query_filter = None
            if filter_source:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="source",
                            match=MatchValue(value=filter_source)
                        )
                    ]
                )
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True
            )
            
            # Convert to RetrievedChunk objects
            retrieved_chunks = []
            for result in results:
                metadata = ChunkMetadata(
                    source=result.payload.get("source", ""),
                    title=result.payload.get("title", ""),
                    section=result.payload.get("section", ""),
                    chunk_id=result.payload.get("chunk_id", ""),
                    links=result.payload.get("links", []),
                    images=result.payload.get("images", []),
                    created_at=result.payload.get("created_at", "")
                )
                
                chunk = RetrievedChunk(
                    chunk_id=result.payload.get("chunk_id", ""),
                    text=result.payload.get("text", ""),
                    score=result.score,
                    metadata=metadata
                )
                retrieved_chunks.append(chunk)
            
            logger.info(f"✓ Retrieved {len(retrieved_chunks)} chunks (top_k={top_k})")
            return retrieved_chunks
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise
    
    def count_points(self) -> int:
        """
        Count total points in collection.
        
        Returns:
            Number of points
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count or 0
        except Exception as e:
            logger.error(f"Error counting points: {e}")
            return 0


# Global instance
_vectorstore_service = None


def get_vectorstore_service() -> VectorStoreService:
    """
    Get or create the global VectorStoreService instance.
    
    Returns:
        VectorStoreService instance
    """
    global _vectorstore_service
    if _vectorstore_service is None:
        _vectorstore_service = VectorStoreService()
    return _vectorstore_service