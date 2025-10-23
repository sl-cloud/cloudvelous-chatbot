"""
Generation service for RAG-based answer generation.

Coordinates retrieval and LLM generation with prompt engineering.
"""

from typing import List, Optional
from app.llm.base import ILLMProvider
from app.services.retriever import RetrievalResult


class GeneratorService:
    """Service for generating answers using RAG pipeline."""
    
    def __init__(self, llm_provider: ILLMProvider):
        """
        Initialize the generator service.
        
        Args:
            llm_provider: LLM provider instance
        """
        self.llm_provider = llm_provider
    
    def _build_context(self, retrieval_results: List[RetrievalResult]) -> str:
        """
        Build context from retrieved chunks.
        
        Args:
            retrieval_results: List of retrieved chunks
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for result in retrieval_results:
            chunk = result.chunk
            context_parts.append(
                f"[Source: {chunk.repo_name}/{chunk.file_path}]\n"
                f"{chunk.content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _build_system_prompt(self) -> str:
        """
        Build system prompt for the LLM.
        
        Returns:
            System prompt string
        """
        return """You are Cloudvelous Chat Assistant, an AI helper that answers questions about Cloudvelous repositories and projects.

Your task is to provide accurate, helpful answers based on the provided context from repository documentation and code.

Guidelines:
1. Answer based ONLY on the provided context
2. If the context doesn't contain enough information, say so clearly
3. Cite sources by mentioning the repository and file names
4. Be concise but thorough
5. Format your response clearly with proper markdown if needed
6. If the question is unclear, ask for clarification"""
    
    def _build_user_prompt(self, query: str, context: str) -> str:
        """
        Build user prompt with query and context.
        
        Args:
            query: User's question
            context: Retrieved context
            
        Returns:
            User prompt string
        """
        return f"""Context from repositories:

{context}

Question: {query}

Please provide a detailed answer based on the context above."""
    
    def generate_answer(
        self,
        query: str,
        retrieval_results: List[RetrievalResult],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate an answer using RAG.
        
        Args:
            query: User's question
            retrieval_results: Retrieved chunks for context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated answer
        """
        # Build context from retrieved chunks
        context = self._build_context(retrieval_results)
        
        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, context)
        
        # Generate answer
        answer = self.llm_provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return answer
    
    def get_provider_name(self) -> str:
        """Get the LLM provider name."""
        return self.llm_provider.get_provider_name()
    
    def get_model_name(self) -> str:
        """Get the LLM model name."""
        return self.llm_provider.get_model_name()

