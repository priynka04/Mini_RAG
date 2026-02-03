"""
Utilities for extracting and managing metadata (links, images, sections).
"""
import re
import hashlib
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def generate_chunk_id(text: str, source: str, index: int) -> str:
    """
    Generate a unique chunk ID.
    
    Args:
        text: Chunk text
        source: Source document
        index: Chunk index
        
    Returns:
        Unique chunk ID
    """
    # Create hash from source and index for uniqueness
    content = f"{source}_{index}_{text[:100]}"
    hash_obj = hashlib.md5(content.encode())
    return f"chunk_{hash_obj.hexdigest()[:12]}"


def extract_sections_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract sections from text based on markdown-style headings.
    
    This is useful for structured documents where we want to preserve
    section information in metadata.
    
    Args:
        text: Input text
        
    Returns:
        List of sections with title and content
    """
    sections = []
    
    # Pattern to match markdown headings (# Heading, ## Heading, etc.)
    heading_pattern = r'^(#{1,6})\s+(.+)$'
    
    lines = text.split('\n')
    current_section = {
        "level": 0,
        "title": "Introduction",
        "content": []
    }
    
    for line in lines:
        match = re.match(heading_pattern, line)
        
        if match:
            # Save previous section if it has content
            if current_section["content"]:
                current_section["content"] = "\n".join(current_section["content"])
                sections.append(current_section)
            
            # Start new section
            level = len(match.group(1))
            title = match.group(2).strip()
            
            current_section = {
                "level": level,
                "title": title,
                "content": []
            }
        else:
            current_section["content"].append(line)
    
    # Add last section
    if current_section["content"]:
        current_section["content"] = "\n".join(current_section["content"])
        sections.append(current_section)
    
    logger.info(f"Extracted {len(sections)} sections from text")
    return sections


def enrich_chunk_metadata(
    base_metadata: dict,
    chunk_text: str,
    all_links: List[str],
    all_images: List[str]
) -> dict:
    """
    Enrich chunk metadata by finding which links/images appear in this chunk.
    
    Args:
        base_metadata: Base metadata dict
        chunk_text: Text content of this chunk
        all_links: All links from the document
        all_images: All images from the document
        
    Returns:
        Enriched metadata dict
    """
    # Find links that appear in this specific chunk
    chunk_links = []
    for link in all_links:
        if link in chunk_text:
            chunk_links.append(link)
    
    # For images, check if the image reference appears in text
    # (e.g., for markdown: ![alt](image.png))
    chunk_images = []
    for image in all_images:
        if image in chunk_text:
            chunk_images.append(image)
    
    # Update metadata
    enriched = base_metadata.copy()
    enriched["links"] = chunk_links
    enriched["images"] = chunk_images
    enriched["has_links"] = len(chunk_links) > 0
    enriched["has_images"] = len(chunk_images) > 0
    
    return enriched


def create_document_metadata(
    source: str,
    title: str,
    file_type: str,
    total_chunks: int,
    links: List[str],
    images: List[str]
) -> dict:
    """
    Create document-level metadata.
    
    Args:
        source: Source filename
        title: Document title
        file_type: File extension (.pdf, .txt, .md)
        total_chunks: Number of chunks created
        links: All links in document
        images: All images in document
        
    Returns:
        Document metadata dict
    """
    return {
        "source": source,
        "title": title,
        "file_type": file_type,
        "total_chunks": total_chunks,
        "total_links": len(links),
        "total_images": len(images),
        "processed_at": datetime.utcnow().isoformat(),
        "links": links,
        "images": images
    }


def validate_metadata(metadata: dict) -> bool:
    """
    Validate that metadata contains required fields.
    
    Args:
        metadata: Metadata dict to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["source", "chunk_id"]
    
    for field in required_fields:
        if field not in metadata:
            logger.error(f"Missing required metadata field: {field}")
            return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized


def extract_domain_from_url(url: str) -> str:
    """
    Extract domain from URL for display purposes.
    
    Args:
        url: Full URL
        
    Returns:
        Domain name
    """
    # Simple regex to extract domain
    match = re.search(r'https?://([^/]+)', url)
    if match:
        return match.group(1)
    return url