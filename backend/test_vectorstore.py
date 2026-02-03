"""
Test script for embeddings and vector store integration.
This script requires valid API keys in .env file.
"""
import sys
from pathlib import Path
# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.embeddings import get_embedding_service
from app.services.vectorstore import get_vectorstore_service
from app.utils.metadata import generate_chunk_id


def test_embedding_service():
    """Test Gemini embeddings."""
    print("\n" + "="*60)
    print("TEST 1: Gemini Embeddings")
    print("="*60)
    
    embedding_service = get_embedding_service()
    
    # Test single embedding
    text = "This is a test document about RAG systems."
    embedding = embedding_service.embed_text(text)
    
    print(f"✓ Text: {text}")
    print(f"✓ Embedding dimension: {len(embedding)}")
    print(f"✓ First 5 values: {embedding[:5]}")
    
    # Test batch embeddings
    texts = [
        "First document about machine learning.",
        "Second document about neural networks.",
        "Third document about transformers."
    ]
    
    batch_embeddings = embedding_service.embed_batch(texts)
    
    print(f"\n✓ Batch embeddings generated: {len(batch_embeddings)}")
    for i, emb in enumerate(batch_embeddings):
        print(f"  - Embedding {i+1}: dimension {len(emb)}")


def test_vectorstore_connection():
    print("\n" + "="*60)
    print("TEST 2: Qdrant Connection")
    print("="*60)

    vectorstore = get_vectorstore_service()

    print("✓ Recreating collection (ensures payload index exists)...")
    vectorstore.create_collection(recreate=True)
    print("✓ Collection recreated successfully")


def test_upsert_and_search():
    """Test upserting and searching."""
    print("\n" + "="*60)
    print("TEST 3: Upsert and Search")
    print("="*60)
    
    embedding_service = get_embedding_service()
    vectorstore = get_vectorstore_service()
    
    vectorstore.delete_by_source("test_doc.txt")
    # Ensure collection exists
    if not vectorstore.collection_exists():
        vectorstore.create_collection()
    
    # Sample data
    chunks = [
        "RAG systems combine retrieval and generation for better AI responses.",
        "Vector databases store embeddings for similarity search.",
        "Chunking is important for managing context window limits."
    ]
    
    # Generate embeddings
    print("✓ Generating embeddings...")
    embeddings = embedding_service.embed_batch(chunks)
    
    # Create metadata
    metadatas = []
    for i, chunk in enumerate(chunks):
        metadata = {
            "chunk_id": generate_chunk_id(chunk, "test_doc.txt", i),
            "source": "test_doc.txt",
            "title": "Test Document",
            "section": "Introduction",
            "links": [],
            "images": []
        }
        metadatas.append(metadata)
    
    # Upsert
    print("✓ Upserting chunks...")
    count = vectorstore.upsert_chunks(chunks, embeddings, metadatas)
    print(f"✓ Upserted {count} chunks")
    
    # Search
    query = "How do RAG systems work?"
    print(f"\n✓ Searching for: '{query}'")
    
    query_embedding = embedding_service.embed_query(query)
    results = vectorstore.search(query_embedding, top_k=2)
    
    print(f"✓ Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"\n  Result {i+1}:")
        print(f"  - Score: {result.score:.4f}")
        print(f"  - Text: {result.text[:80]}...")
        print(f"  - Source: {result.metadata.source}")


def test_delete_by_source():
    """Test deleting chunks by source."""
    print("\n" + "="*60)
    print("TEST 4: Delete by Source")
    print("="*60)
    
    vectorstore = get_vectorstore_service()
    
    print("✓ Points before deletion:")
    count_before = vectorstore.count_points()
    print(f"  - Total points: {count_before}")
    
    # Delete test document
    print("\n✓ Deleting 'test_doc.txt'...")
    vectorstore.delete_by_source("test_doc.txt")
    
    print("✓ Points after deletion:")
    count_after = vectorstore.count_points()
    print(f"  - Total points: {count_after}")
    print(f"  - Deleted: {count_before - count_after}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING EMBEDDINGS AND VECTOR STORE")
    print("="*60)
    print("\n⚠️  This test requires valid API keys in .env file:")
    print("   - GOOGLE_API_KEY")
    print("   - QDRANT_URL")
    print("   - QDRANT_API_KEY")
    print()
    
    try:
        test_embedding_service()
        test_vectorstore_connection()
        test_upsert_and_search()
        test_delete_by_source()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Make sure you have:")
        print("   1. Valid API keys in .env file")
        print("   2. Active internet connection")
        print("   3. Qdrant Cloud cluster running")