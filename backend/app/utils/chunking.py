"""
Token-based text chunking with configurable size and overlap.
Uses tiktoken for accurate token counting.
"""
import tiktoken
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Token-based text chunker with overlap.
    
    Implements the chunking strategy:
    - Chunk size: 1000 tokens
    - Overlap: 120 tokens (~12%)
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 120,
        encoding_name: str = "cl100k_base"  # Used by text-embedding-3-small
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
            encoding_name: Tiktoken encoding to use
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Could not load encoding {encoding_name}, using cl100k_base: {e}")
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info(f"Initialized TextChunker: size={chunk_size}, overlap={chunk_overlap}")
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks based on token count.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        # Encode text to tokens
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)
        
        if total_tokens <= self.chunk_size:
            # Text is small enough to be a single chunk
            return [text]
        
        chunks = []
        start = 0
        
        while start < total_tokens:
            # Define end position
            end = start + self.chunk_size
            
            # Extract chunk tokens
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # Move start position with overlap
            # If this is the last possible chunk, break
            if end >= total_tokens:
                break
            
            start = end - self.chunk_overlap
        
        logger.info(f"Created {len(chunks)} chunks from {total_tokens} tokens")
        return chunks
    
    def chunk_text_with_metadata(
        self,
        text: str,
        source: str,
        title: str = "",
        section: str = ""
    ) -> List[Tuple[str, dict]]:
        """
        Chunk text and return chunks with basic metadata.
        
        Args:
            text: Input text to chunk
            source: Source document name
            title: Document title
            section: Section name (optional)
            
        Returns:
            List of (chunk_text, metadata) tuples
        """
        chunks = self.chunk_text(text)
        
        chunks_with_metadata = []
        for idx, chunk in enumerate(chunks):
            metadata = {
                "source": source,
                "title": title,
                "section": section,
                "chunk_index": idx,
                "total_chunks": len(chunks)
            }
            chunks_with_metadata.append((chunk, metadata))
        
        return chunks_with_metadata
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
    
    def estimate_chunks(self, text: str) -> int:
        """
        Estimate number of chunks that will be created.
        
        Args:
            text: Input text
            
        Returns:
            Estimated number of chunks
        """
        total_tokens = self.count_tokens(text)
        
        if total_tokens <= self.chunk_size:
            return 1
        
        # Calculate chunks considering overlap
        # Formula: ceil((total - chunk_size) / (chunk_size - overlap)) + 1
        effective_size = self.chunk_size - self.chunk_overlap
        remaining_tokens = total_tokens - self.chunk_size
        
        additional_chunks = (remaining_tokens + effective_size - 1) // effective_size
        return 1 + additional_chunks


def create_chunks_from_document(
    text: str,
    source: str,
    title: str = "",
    links: List[str] = None,
    images: List[str] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 120
) -> List[Tuple[str, dict]]:
    """
    Convenience function to create chunks with full metadata.
    
    This function distributes links and images to their nearest chunks
    based on character position in the original text.
    
    Args:
        text: Input text to chunk
        source: Source document name
        title: Document title
        links: List of URLs found in document
        images: List of image references
        chunk_size: Maximum tokens per chunk
        chunk_overlap: Overlap in tokens
        
    Returns:
        List of (chunk_text, full_metadata) tuples
    """
    links = links or []
    images = images or []
    
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.chunk_text(text)
    
    chunks_with_metadata = []
    
    for idx, chunk in enumerate(chunks):
        # Assign links that appear in this chunk
        chunk_links = [link for link in links if link in chunk]
        
        # For images, we'll distribute them evenly across chunks
        # (since we don't have exact positions)
        chunk_images = []
        if images:
            # Simple distribution: assign images proportionally
            images_per_chunk = max(1, len(images) // len(chunks))
            start_img = idx * images_per_chunk
            end_img = start_img + images_per_chunk
            chunk_images = images[start_img:end_img]
        
        metadata = {
            "source": source,
            "title": title,
            "section": "",
            "chunk_index": idx,
            "total_chunks": len(chunks),
            "links": chunk_links,
            "images": chunk_images
        }
        
        chunks_with_metadata.append((chunk, metadata))
    
    logger.info(f"Created {len(chunks_with_metadata)} chunks with metadata for '{source}'")
    return chunks_with_metadata