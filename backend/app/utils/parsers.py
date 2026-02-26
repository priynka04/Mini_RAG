"""
Document parsers for extracting text, links, and images from various file formats.
"""
import re
from typing import Dict, List, Tuple
from pathlib import Path
import logging

# PDF parsing
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class ParsedDocument:
    """Container for parsed document content and metadata."""
    
    def __init__(self, text: str, links: List[str], images: List[str], title: str = ""):
        self.text = text
        self.links = links
        self.images = images
        self.title = title
    
    def __repr__(self):
        return (f"ParsedDocument(title={self.title}, "
                f"text_length={len(self.text)}, "
                f"links={len(self.links)}, "
                f"images={len(self.images)})")


class DocumentParser:
    @staticmethod    
    def parse_pdf(file_path: str) -> ParsedDocument:
         try:
             reader = PdfReader(file_path)

             text_parts = []
             all_links = []
             image_references = []

            for page_num, page in enumerate(reader.pages, 1):
                 page_text = page.extract_text()
                 if page_text:
                    text_parts.append(page_text)

                 if "/Annots" in page:
                  for annotation in page["/Annots"]:
                    obj = annotation.get_object()
                    if "/A" in obj and "/URI" in obj["/A"]:
                        uri = obj["/A"]["/URI"]
                        if uri and uri not in all_links:
                            all_links.append(uri)

                 if "/Resources" in page and "/XObject" in page["/Resources"]:
                  xobjects = page["/Resources"]["/XObject"].get_object()
                  for obj_name in xobjects:
                    obj = xobjects[obj_name]
                    if obj.get("/Subtype") == "/Image":
                        image_references.append(f"page_{page_num}_{obj_name}")

            full_text = "\n\n".join(text_parts)

        # ✅ OCR FALLBACK (CORRECT INDENTATION)
            if not full_text.strip():
                logger.warning("No text found via pypdf. Falling back to OCR...")

                 from pdf2image import convert_from_path
                 import pytesseract

                 images = convert_from_path(file_path)
                 ocr_text = []

                 for img in images:
                     text = pytesseract.image_to_string(img)
                     if text.strip():
                        ocr_text.append(text)

                 full_text = "\n".join(ocr_text)

            metadata = reader.metadata
            title = metadata.title if metadata and metadata.title else Path(file_path).stem

            text_links = DocumentParser._extract_urls_from_text(full_text)
            all_links.extend([l for l in text_links if l not in all_links])

            logger.info(
                f"Parsed PDF: {len(reader.pages)} pages, "
                f"{len(all_links)} links, {len(image_references)} images"
             )

             return ParsedDocument(
                 text=full_text,
                 links=all_links,
                 images=image_references,
                 title=title
             )

    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        raise
    
    @staticmethod
    def parse_text(file_path: str) -> ParsedDocument:
        """
        Parse plain text file and extract URLs.
        
        Args:
            file_path: Path to text file
            
        Returns:
            ParsedDocument with extracted content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Extract URLs from text
            links = DocumentParser._extract_urls_from_text(text)
            
            # Text files don't have images
            images = []
            
            # Use filename as title
            title = Path(file_path).stem
            
            logger.info(f"Parsed TXT: {len(text)} chars, {len(links)} links")
            
            return ParsedDocument(
                text=text,
                links=links,
                images=images,
                title=title
            )
            
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {e}")
            raise
    
    @staticmethod
    def parse_markdown(file_path: str) -> ParsedDocument:
        """
        Parse Markdown file and extract text, links, and image references.
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            ParsedDocument with extracted content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Extract markdown links [text](url)
            md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
            links = [url for _, url in md_links if url.startswith('http')]
            
            # Extract markdown images ![alt](image_path)
            md_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', text)
            images = [img_path for _, img_path in md_images]
            
            # Also extract plain URLs from text
            text_links = DocumentParser._extract_urls_from_text(text)
            links.extend([link for link in text_links if link not in links])
            
            # Use filename as title, or extract from first # heading
            title = Path(file_path).stem
            heading_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
            if heading_match:
                title = heading_match.group(1).strip()
            
            logger.info(f"Parsed Markdown: {len(text)} chars, "
                       f"{len(links)} links, {len(images)} images")
            
            return ParsedDocument(
                text=text,
                links=links,
                images=images,
                title=title
            )
            
        except Exception as e:
            logger.error(f"Error parsing markdown file {file_path}: {e}")
            raise
    
    @staticmethod
    def parse_raw_text(text: str, title: str = "Pasted Text") -> ParsedDocument:
        """
        Parse raw text content (for paste functionality).
        
        Args:
            text: Raw text content
            title: Optional title
            
        Returns:
            ParsedDocument with extracted content
        """
        # Extract URLs
        links = DocumentParser._extract_urls_from_text(text)
        
        # No images in pasted text
        images = []
        
        logger.info(f"Parsed raw text: {len(text)} chars, {len(links)} links")
        
        return ParsedDocument(
            text=text,
            links=links,
            images=images,
            title=title
        )
    
    @staticmethod
    def _extract_urls_from_text(text: str) -> List[str]:
        """
        Extract URLs from plain text using regex.
        
        Args:
            text: Text content
            
        Returns:
            List of unique URLs
        """
        # Pattern to match URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            # Clean trailing punctuation
            url = url.rstrip('.,;:!?)')
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    @staticmethod
    def parse_file(file_path: str) -> ParsedDocument:
        """
        Parse file based on extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            ParsedDocument with extracted content
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.pdf':
            return DocumentParser.parse_pdf(file_path)
        elif extension == '.txt':
            return DocumentParser.parse_text(file_path)
        elif extension in ['.md', '.markdown']:
            return DocumentParser.parse_markdown(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
