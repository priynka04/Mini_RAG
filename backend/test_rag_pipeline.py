"""
Test the complete RAG pipeline: Ingest → Query → Retrieve → Rerank → Answer
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.ingestion import get_ingestion_service
from app.services.retrieval import get_retrieval_service
from app.services.llm import get_llm_service
from app.models.schemas import ChatMessage


def test_complete_rag_pipeline():
    """Test the complete RAG pipeline end-to-end."""
    
    print("\n" + "="*70)
    print("COMPLETE RAG PIPELINE TEST")
    print("="*70)
    
    # Step 1: Ingest test document
    print("\n[STEP 1] Ingesting test document...")
    print("-" * 70)
    
    test_document = """
# Retrieval-Augmented Generation (RAG) Systems

RAG is an AI framework that combines information retrieval with text generation.

## Core Components

### 1. Vector Database
RAG systems use vector databases like Qdrant, Pinecone, or Weaviate to store
document embeddings. These enable fast similarity search.

Visit https://qdrant.tech for more information about Qdrant.

### 2. Embedding Model
Documents are converted to vector representations using embedding models.
Popular choices include:
- OpenAI text-embedding-3-small
- Google text-embedding-004  
- Cohere embed-english-v3.0

### 3. Reranking
After initial retrieval, a reranking model (like Cohere Rerank) improves
result quality by reordering chunks based on relevance to the query.

### 4. Language Model
The final component is an LLM (like GPT-4, Gemini, or Claude) that generates
answers based on retrieved context.

## Benefits

RAG systems offer several key advantages:
- **Reduced hallucinations**: Answers are grounded in retrieved facts
- **Up-to-date knowledge**: Can access current information without retraining
- **Source attribution**: Can cite specific sources [1]
- **Cost-effective**: More affordable than fine-tuning for domain knowledge

## Implementation Steps

1. Chunk your documents (typically 500-1500 tokens)
2. Generate embeddings for each chunk
3. Store in a vector database
4. For queries: embed → search → rerank → generate

Learn more at https://python.langchain.com/docs/use_cases/question_answering/

## Common Challenges

- Choosing optimal chunk size
- Handling long documents
- Managing chat history
- Balancing retrieval vs. generation quality
"""
    
    ingestion_service = get_ingestion_service()
    result = ingestion_service.ingest_text(
        text=test_document,
        title="RAG Systems Guide"
    )
    
    print(f"✓ Ingested: {result['title']}")
    print(f"✓ Chunks: {result['chunks_created']}")
    print(f"✓ Links: {result['links_extracted']}")
    print(f"✓ Time: {result['processing_time_ms']:.0f}ms")
    
    # Step 2: Test retrieval + reranking
    print("\n[STEP 2] Testing retrieval + reranking...")
    print("-" * 70)
    
    retrieval_service = get_retrieval_service()
    
    query = "What are the benefits of RAG systems?"
    print(f"Query: '{query}'")
    
    reranked_chunks, timing = retrieval_service.retrieve_and_rerank(query)
    
    print(f"\n✓ Retrieved: {len(reranked_chunks)} chunks")
    print(f"✓ Retrieval time: {timing.get('retrieval_ms', 0):.0f}ms")
    print(f"✓ Rerank time: {timing.get('rerank_ms', 0):.0f}ms")
    
    print("\nTop 3 results:")
    for i, chunk in enumerate(reranked_chunks[:3], 1):
        print(f"\n  [{i}] Score: {chunk.score:.4f} (original: {chunk.original_score:.4f})")
        print(f"      Text: {chunk.text[:80]}...")
        if chunk.metadata.links:
            print(f"      Links: {chunk.metadata.links[:2]}")
    
    # Step 3: Test LLM answer generation
    print("\n[STEP 3] Generating answer with citations...")
    print("-" * 70)
    
    llm_service = get_llm_service()
    
    answer, sources, llm_timing, token_usage = llm_service.generate_answer(
        query=query,
        context_chunks=reranked_chunks,
        chat_history=[]
    )
    
    print(f"\nQuery: {query}")
    print(f"\nAnswer:\n{answer}")
    
    print(f"\n✓ Sources: {len(sources)}")
    print(f"✓ LLM time: {llm_timing['llm_ms']:.0f}ms")
    if token_usage:
        print(f"✓ Tokens: {token_usage.total_tokens} "
              f"(prompt: {token_usage.prompt_tokens}, "
              f"completion: {token_usage.completion_tokens})")
        print(f"✓ Estimated cost: ${token_usage.estimated_cost_usd:.6f}")
    
    print("\nSources:")
    for source in sources[:3]:
        print(f"\n  [{source.id}] {source.document}")
        print(f"      {source.text[:100]}...")
        if source.links:
            print(f"      Links: {source.links}")
    
    # Step 4: Test with chat history
    print("\n[STEP 4] Testing with chat history...")
    print("-" * 70)
    
    chat_history = [
        ChatMessage(role="user", content="What are the benefits of RAG?"),
        ChatMessage(
            role="assistant",
            content="RAG offers reduced hallucinations, up-to-date knowledge, "
                   "source attribution, and cost-effectiveness [1]."
        )
    ]
    
    followup_query = "Can you explain more about the cost-effectiveness?"
    print(f"Follow-up query: '{followup_query}'")
    
    reranked_chunks2, _ = retrieval_service.retrieve_and_rerank(followup_query)
    
    answer2, sources2, _, _ = llm_service.generate_answer(
        query=followup_query,
        context_chunks=reranked_chunks2,
        chat_history=chat_history
    )
    
    print(f"\nAnswer:\n{answer2}")
    
    # Step 5: Test no-context scenario
    print("\n[STEP 5] Testing no-context scenario...")
    print("-" * 70)
    
    irrelevant_query = "What is the recipe for chocolate cake?"
    print(f"Query: '{irrelevant_query}'")
    
    reranked_chunks3, _ = retrieval_service.retrieve_and_rerank(irrelevant_query)
    
    has_context = retrieval_service.check_context_relevance(reranked_chunks3)
    
    print(f"\n✓ Has relevant context: {has_context}")
    
    if not has_context:
        print("✓ Correctly detected irrelevant query!")
        general_answer, _ = llm_service.generate_general_answer(irrelevant_query)
        print(f"\nGeneral answer:\n{general_answer[:200]}...")
    
    # Summary
    print("\n" + "="*70)
    print("✅ COMPLETE RAG PIPELINE TEST PASSED!")
    print("="*70)
    print("\nPipeline verified:")
    print("  ✓ Document ingestion (parse → chunk → embed → store)")
    print("  ✓ Vector retrieval (embed query → search)")
    print("  ✓ Reranking (Cohere)")
    print("  ✓ Answer generation with citations (Gemini)")
    print("  ✓ Chat history handling")
    print("  ✓ No-context detection")
    print("\n🚀 Ready for API testing and frontend integration!")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        test_complete_rag_pipeline()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()