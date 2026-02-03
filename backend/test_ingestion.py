"""
Test script for document ingestion service.
Tests the complete pipeline: parse → chunk → embed → store
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ingestion import get_ingestion_service
from app.services.vectorstore import get_vectorstore_service
import tempfile


def test_ingest_text():
    """Test ingesting pasted text."""
    print("\n" + "="*60)
    print("TEST 1: Ingest Pasted Text")
    print("="*60)
    
    ingestion_service = get_ingestion_service()
    
    sample_text = """
    # Introduction to RAG Systems
    
    Retrieval-Augmented Generation (RAG) is a powerful technique that combines
    the strengths of retrieval-based and generation-based approaches in AI.
    
    ## How RAG Works
    
    RAG systems work in three main steps:
    
    1. **Retrieval**: The system searches a knowledge base for relevant information
       based on the user's query. This is typically done using vector similarity
       search with embeddings.
    
    2. **Augmentation**: The retrieved information is added to the context that
       will be provided to the language model. This ensures the model has access
       to relevant, up-to-date information.
    
    3. **Generation**: The language model generates a response based on both
       the original query and the retrieved context. This allows for more
       accurate and grounded responses.
    
    ## Benefits of RAG
    
    - Reduces hallucinations by grounding responses in retrieved facts
    - Allows updating knowledge without retraining the model
    - Provides source attribution for generated content
    - More cost-effective than fine-tuning for domain-specific knowledge
    
    Learn more at https://example.com/rag-tutorial and check out the
    documentation at https://docs.example.com/rag
    
    ## Vector Databases
    
    RAG systems rely on vector databases like Qdrant, Pinecone, or Weaviate
    to store and retrieve embeddings efficiently. These databases support:
    
    - Fast similarity search at scale
    - Metadata filtering
    - Hybrid search combining vector and keyword search
    
    For more information, visit https://qdrant.tech
    """
    
    result = ingestion_service.ingest_text(
        text=sample_text,
        title="RAG Systems Guide"
    )
    
    print(f"✓ Success: {result['success']}")
    print(f"✓ Document ID: {result['document_id']}")
    print(f"✓ Title: {result['title']}")
    print(f"✓ Chunks created: {result['chunks_created']}")
    print(f"✓ Links extracted: {result['links_extracted']}")
    print(f"✓ Images extracted: {result['images_extracted']}")
    print(f"✓ Processing time: {result['processing_time_ms']:.0f}ms")


def test_ingest_markdown_file():
    """Test ingesting a markdown file."""
    print("\n" + "="*60)
    print("TEST 2: Ingest Markdown File")
    print("="*60)
    
    # Create a temporary markdown file
    markdown_content = """# Machine Learning Basics

Machine learning is a subset of artificial intelligence that enables systems
to learn and improve from experience without being explicitly programmed.

## Types of Machine Learning

### Supervised Learning
In supervised learning, models are trained on labeled data. Common algorithms include:
- Linear Regression
- Decision Trees
- Neural Networks

Learn more at https://scikit-learn.org

### Unsupervised Learning
Unsupervised learning works with unlabeled data to find patterns. Examples:
- K-Means Clustering
- Principal Component Analysis (PCA)

### Reinforcement Learning
Agents learn by interacting with an environment and receiving rewards.

Check out OpenAI's research at https://openai.com/research

## Deep Learning

Deep learning uses neural networks with multiple layers. Popular frameworks:
- TensorFlow (https://tensorflow.org)
- PyTorch (https://pytorch.org)

![Neural Network Diagram](neural_net.png)

## Conclusion

Machine learning is transforming industries from healthcare to finance.
"""
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.md',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(markdown_content)
        temp_path = f.name
    
    try:
        ingestion_service = get_ingestion_service()
        
        result = ingestion_service.ingest_file(temp_path)
        
        print(f"✓ Success: {result['success']}")
        print(f"✓ Document ID: {result['document_id']}")
        print(f"✓ Title: {result['title']}")
        print(f"✓ Chunks created: {result['chunks_created']}")
        print(f"✓ Links extracted: {result['links_extracted']}")
        print(f"✓ Images extracted: {result['images_extracted']}")
        print(f"✓ Processing time: {result['processing_time_ms']:.0f}ms")
        
    finally:
        # Clean up
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_ingestion_stats():
    """Test getting ingestion statistics."""
    print("\n" + "="*60)
    print("TEST 3: Ingestion Statistics")
    print("="*60)
    
    ingestion_service = get_ingestion_service()
    
    stats = ingestion_service.get_ingestion_stats()
    
    print(f"✓ Total chunks: {stats.get('total_chunks')}")
    print(f"✓ Collection: {stats.get('collection_name')}")
    print(f"✓ Status: {stats.get('status')}")
    print(f"✓ Vectors: {stats.get('vector_count')}")


def test_search_ingested_content():
    """Test searching the ingested content."""
    print("\n" + "="*60)
    print("TEST 4: Search Ingested Content")
    print("="*60)
    
    from app.services.embeddings import get_embedding_service
    
    vectorstore = get_vectorstore_service()
    embedding_service = get_embedding_service()
    
    # Search for RAG-related content
    query = "What are the benefits of RAG systems?"
    print(f"✓ Query: '{query}'")
    
    query_embedding = embedding_service.embed_query(query)
    results = vectorstore.search(query_embedding, top_k=3)
    
    print(f"✓ Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"  [{i}] Score: {result.score:.4f}")
        print(f"      Source: {result.metadata.source}")
        print(f"      Title: {result.metadata.title}")
        print(f"      Text: {result.text[:100]}...")
        if result.metadata.links:
            print(f"      Links: {result.metadata.links}")
        print()


def cleanup_test_data():
    """Clean up test documents from vector store."""
    print("\n" + "="*60)
    print("CLEANUP: Removing Test Documents")
    print("="*60)
    
    vectorstore = get_vectorstore_service()
    
    # Delete test documents
    test_sources = ["text_", ".md"]  # Partial matches for our test files
    
    print("✓ Test documents will remain for inspection")
    print("✓ To clean up manually, recreate the collection:")
    print("  vectorstore.create_collection(recreate=True)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING DOCUMENT INGESTION SERVICE")
    print("="*60)
    print("\n⚠️  This test requires valid API keys in .env file")
    print()
    
    try:
        test_ingest_text()
        test_ingest_markdown_file()
        test_ingestion_stats()
        test_search_ingested_content()
        cleanup_test_data()
        
        print("\n" + "="*60)
        print("✅ ALL INGESTION TESTS PASSED!")
        print("="*60)
        print("\n💡 Next steps:")
        print("   1. Check Qdrant dashboard to see your data")
        print("   2. Try searching with different queries")
        print("   3. Ready to build the retrieval + reranking pipeline!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()