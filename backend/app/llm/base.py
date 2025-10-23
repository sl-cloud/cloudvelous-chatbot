"""
Base LLM provider interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class ILLMProvider(ABC):
    """Interface for LLM providers."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate text from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name.
        
        Returns:
            Provider name (e.g., "openai", "gemini")
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the model name.
        
        Returns:
            Model name (e.g., "gpt-4", "gemini-pro")
        """
        pass

