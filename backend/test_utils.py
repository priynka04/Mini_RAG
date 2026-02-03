"""
Test script for parsing and chunking utilities.
Run this to verify the utilities work correctly.
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.parsers import DocumentParser
from app.utils.chunking import TextChunker, create_chunks_from_document
from app.utils.metadata import generate_chunk_id, extract_sections_from_text


def test_text_parsing():
    """Test parsing of raw text."""
    print("\n" + "="*60)
    print("TEST 1: Raw Text Parsing")
    print("="*60)
    
    sample_text = """
    This is a sample document about RAG systems.
    
    You can learn more at https://example.com/rag and also check
    https://docs.example.com for documentation.
    
    RAG stands for Retrieval-Augmented Generation.
    """
    
    parsed = DocumentParser.parse_raw_text(sample_text, "Sample Document")
    
    print(f"✓ Text length: {len(parsed.text)} chars")
    print(f"✓ Links found: {len(parsed.links)}")
    for link in parsed.links:
        print(f"  - {link}")
    print(f"✓ Title: {parsed.title}")
    

def test_chunking():
    """Test text chunking."""
    print("\n" + "="*60)
    print("TEST 2: Text Chunking")
    print("="*60)
    
    # Create a longer text
    long_text = " ".join([
        "This is sentence number {}.".format(i) 
        for i in range(1, 500)
    ])
    
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    
    print(f"✓ Original text tokens: {chunker.count_tokens(long_text)}")
    
    chunks = chunker.chunk_text(long_text)
    
    print(f"✓ Chunks created: {len(chunks)}")
    print(f"✓ First chunk (100 chars): {chunks[0][:100]}...")
    print(f"✓ First chunk tokens: {chunker.count_tokens(chunks[0])}")
    
    if len(chunks) > 1:
        print(f"✓ Second chunk tokens: {chunker.count_tokens(chunks[1])}")


def test_chunks_with_metadata():
    """Test chunking with metadata."""
    print("\n" + "="*60)
    print("TEST 3: Chunking with Metadata")
    print("="*60)
    
    sample_text = """
    # Introduction to RAG
    
    RAG systems combine retrieval and generation. Learn more at https://example.com/rag
    
    ## How it Works
    
    The system retrieves relevant documents and uses them to generate answers.
    See the architecture diagram at https://example.com/architecture
    """
    
    links = ["https://example.com/rag", "https://example.com/architecture"]
    images = ["diagram.png"]
    
    chunks_with_meta = create_chunks_from_document(
        text=sample_text,
        source="rag_intro.md",
        title="RAG Introduction",
        links=links,
        images=images,
        chunk_size=100,
        chunk_overlap=20
    )
    
    print(f"✓ Chunks with metadata: {len(chunks_with_meta)}")
    
    for idx, (chunk, metadata) in enumerate(chunks_with_meta):
        print(f"\n  Chunk {idx + 1}:")
        print(f"    - Source: {metadata['source']}")
        print(f"    - Title: {metadata['title']}")
        print(f"    - Links: {metadata['links']}")
        print(f"    - Images: {metadata['images']}")
        print(f"    - Text preview: {chunk[:80]}...")


def test_chunk_id_generation():
    """Test chunk ID generation."""
    print("\n" + "="*60)
    print("TEST 4: Chunk ID Generation")
    print("="*60)
    
    chunk_id = generate_chunk_id("Sample text", "document.pdf", 0)
    print(f"✓ Generated chunk ID: {chunk_id}")
    
    # Test uniqueness
    chunk_id_2 = generate_chunk_id("Sample text", "document.pdf", 1)
    print(f"✓ Different index ID: {chunk_id_2}")
    
    assert chunk_id != chunk_id_2, "IDs should be different for different indices"
    print("✓ IDs are unique")


def test_section_extraction():
    """Test section extraction from markdown."""
    print("\n" + "="*60)
    print("TEST 5: Section Extraction")
    print("="*60)
    
    markdown_text = """
# Main Title

Introduction paragraph.

## Section 1

Content of section 1.

## Section 2

Content of section 2.

### Subsection 2.1

Subsection content.
"""
    
    sections = extract_sections_from_text(markdown_text)
    
    print(f"✓ Sections found: {len(sections)}")
    for section in sections:
        print(f"  - Level {section['level']}: {section['title']}")
        print(f"    Content length: {len(section['content'])} chars")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING PARSING AND CHUNKING UTILITIES")
    print("="*60)
    
    try:
        test_text_parsing()
        test_chunking()
        test_chunks_with_metadata()
        test_chunk_id_generation()
        test_section_extraction()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()