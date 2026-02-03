"""
LLM service for generating answers with inline citations.
Uses Google Gemini with carefully crafted prompts.
"""
import time
from typing import List, Dict, Any, Tuple, Optional
import logging
import google.generativeai as genai

from app.config import settings
from app.models.schemas import RerankedChunk, ChatMessage, SourceReference, TokenUsage

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for generating answers using Google Gemini.
    
    Features:
    - Inline citations [1], [2], etc.
    - Source attribution
    - Chat history support
    - No-answer detection
    """
    
    def __init__(self):
        """Initialize Gemini client."""
        genai.configure(api_key=settings.google_api_key)
        
        # Use the model name from settings - try common formats
        model_name = settings.llm_model
        
        # Try different model name formats
        possible_names = [
            model_name,
            f"models/{model_name}",
            "gemini-1.5-flash",
            "models/gemini-1.5-flash",
            "gemini-pro",
            "models/gemini-pro"
        ]
        
        self.model = None
        for name in possible_names:
            try:
                self.model = genai.GenerativeModel(
                    model_name=name,
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 2048,
                    }
                )
                # Test if model works
                self.model.count_tokens("test")
                self.model_name = name
                logger.info(f"LLMService initialized with model: {name}")
                break
            except Exception as e:
                continue
        
        if self.model is None:
            raise ValueError(
                f"Could not initialize Gemini model. Tried: {possible_names}. "
                f"Run 'python list_models.py' to see available models."
            )
    
    def generate_answer(
        self,
        query: str,
        context_chunks: List[RerankedChunk],
        chat_history: Optional[List[ChatMessage]] = None
    ) -> Tuple[str, List[SourceReference], dict, Optional[TokenUsage]]:
        """
        Generate answer with inline citations.
        
        Args:
            query: User query
            context_chunks: Reranked chunks to use as context
            chat_history: Previous conversation turns
            
        Returns:
            Tuple of (answer, source_references, timing, token_usage)
        """
        start_time = time.time()
        
        # Build prompt
        prompt = self._build_prompt(query, context_chunks, chat_history or [])
        
        # Generate response
        logger.info("Generating answer with Gemini...")
        
        try:
            response = self.model.generate_content(prompt)
            answer = response.text
            
            timing = {
                'llm_ms': (time.time() - start_time) * 1000
            }
            
            # Create source references
            sources = self._create_source_references(context_chunks)
            
            # Estimate token usage (Gemini API doesn't provide exact counts in free tier)
            token_usage = self._estimate_token_usage(prompt, answer)
            
            logger.info(f"✓ Answer generated ({timing['llm_ms']:.0f}ms)")
            
            return answer, sources, timing, token_usage
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
    
    def generate_general_answer(
        self,
        query: str
    ) -> Tuple[str, dict]:
        """
        Generate general knowledge answer (when no relevant context found).
        
        Args:
            query: User query
            
        Returns:
            Tuple of (answer, timing)
        """
        start_time = time.time()
        
        prompt = f"""You are a helpful AI assistant. The user has asked a question, but there is no relevant information in the uploaded documents to answer it.

Please provide a helpful answer based on your general knowledge, but make it VERY CLEAR that this answer is NOT based on the uploaded documents.

User question: {query}

Important:
- Start your answer with a clear disclaimer
- Use phrases like "Based on general knowledge" or "From what I know generally"
- Keep the answer concise and helpful
- Do not mention any specific documents or sources"""

        try:
            response = self.model.generate_content(prompt)
            answer = response.text
            
            timing = {
                'llm_ms': (time.time() - start_time) * 1000
            }
            
            return answer, timing
            
        except Exception as e:
            logger.error(f"Error generating general answer: {e}")
            return (
                "I don't have information about this in the uploaded documents, "
                "and I encountered an error generating a general response.",
                {'llm_ms': 0}
            )
    
    def _build_prompt(
        self,
        query: str,
        context_chunks: List[RerankedChunk],
        chat_history: List[ChatMessage]
    ) -> str:
        """Build the complete prompt for the LLM."""
        
        # System instructions
        system_prompt = """You are a knowledgeable and friendly AI assistant that helps users understand their documents through engaging, conversational answers.

CRITICAL RULES:
1. Answer ONLY using information from the provided context
2. ALWAYS use inline citations [1], [2], [3] after every claim or fact
3. Write in a natural, conversational tone - like explaining to a colleague
4. Structure longer answers with clear paragraphs for readability
5. When relevant, provide examples or clarifications from the context
6. If the context mentions links, naturally incorporate them: "You can learn more at [URL]"
7. If the context mentions images, reference them: "as illustrated in the diagram [1]"
8. If the context is insufficient, honestly say: "I don't have enough information in the uploaded documents to fully answer this."
9. NEVER make up information beyond what's in the context

FORMATTING GUIDELINES:
- Use inline citations like [1], [2] immediately after each fact
- Keep paragraphs focused (2-4 sentences each)
- Use natural language, avoid robotic phrasing
- When listing items, present them in sentence form with citations
- Make your answer engaging and easy to follow

CITATION EXAMPLES:
✓ Good: "Deep learning uses neural networks with multiple layers [1]. Popular frameworks include TensorFlow and PyTorch [2]."
✓ Good: "The system offers three main benefits: reduced hallucinations [1], up-to-date knowledge [2], and cost-effectiveness [3]."
✗ Bad: "Deep learning uses neural networks. Popular frameworks include TensorFlow and PyTorch." (missing citations)
"""
        
        # Format context chunks
        context_text = "\n\n".join([
            f"[{i+1}] Source: {chunk.metadata.source}\n"
            f"Title: {chunk.metadata.title}\n"
            f"Text: {chunk.text}\n"
            f"Links: {', '.join(chunk.metadata.links) if chunk.metadata.links else 'None'}\n"
            f"Images: {', '.join(chunk.metadata.images) if chunk.metadata.images else 'None'}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Format chat history
        history_text = ""
        if chat_history:
            history_messages = []
            for msg in chat_history[-settings.chat_history_turns:]:
                role = "User" if msg.role == "user" else "Assistant"
                history_messages.append(f"{role}: {msg.content}")
            history_text = "\n\nPrevious conversation:\n" + "\n".join(history_messages)
        
        # Complete prompt
        full_prompt = f"""{system_prompt}

CONTEXT FROM UPLOADED DOCUMENTS:
{context_text}
{history_text}

CURRENT USER QUESTION: {query}

YOUR ANSWER (conversational, well-structured, with inline citations):"""
        
        return full_prompt
    
    def _create_source_references(
        self,
        chunks: List[RerankedChunk]
    ) -> List[SourceReference]:
        """Create source reference objects from chunks."""
        sources = []
        
        for i, chunk in enumerate(chunks):
            source = SourceReference(
                id=i + 1,
                text=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                document=chunk.metadata.source,
                links=chunk.metadata.links,
                images=chunk.metadata.images,
                score=chunk.score,
                chunk_id=chunk.chunk_id,
                section=chunk.metadata.section
            )
            sources.append(source)
        
        return sources
    
    def _estimate_token_usage(
        self,
        prompt: str,
        answer: str
    ) -> TokenUsage:
        """
        Estimate token usage (Gemini free tier doesn't provide exact counts).
        
        Rough estimation: 1 token ≈ 4 characters
        """
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(answer) // 4
        total_tokens = prompt_tokens + completion_tokens
        
        # Gemini pricing (for reference, free tier has no cost)
        # Gemini 1.5 Flash: $0.075 / 1M input tokens, $0.30 / 1M output tokens
        input_cost = (prompt_tokens / 1_000_000) * 0.075
        output_cost = (completion_tokens / 1_000_000) * 0.30
        estimated_cost = input_cost + output_cost
        
        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost
        )


# Global instance
_llm_service = None


def get_llm_service() -> LLMService:
    """
    Get or create the global LLMService instance.
    
    Returns:
        LLMService instance
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service