"""
LLM provider factory for dependency injection.
"""

from app.llm.base import ILLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.gemini_provider import GeminiProvider
from app.config import settings


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""
    
    @staticmethod
    def create_provider(provider_name: str = None) -> ILLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_name: Name of the provider ("openai" or "gemini")
                          If None, uses settings.LLM_PROVIDER
            
        Returns:
            ILLMProvider instance
            
        Raises:
            ValueError: If provider name is not supported
        """
        if provider_name is None:
            provider_name = settings.LLM_PROVIDER
        
        provider_name = provider_name.lower()
        
        if provider_name == "openai":
            return OpenAIProvider()
        elif provider_name == "gemini":
            return GeminiProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")


# Global provider instance
_provider_instance = None


def get_llm_provider() -> ILLMProvider:
    """
    Get or create the global LLM provider instance.
    
    Returns:
        ILLMProvider instance
    """
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = LLMProviderFactory.create_provider()
    return _provider_instance

