"""
OpenAI LLM provider implementation.
"""

from typing import Optional
from openai import OpenAI

from app.llm.base import ILLMProvider
from app.config import settings


class OpenAIProvider(ILLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI provider.
        
        Args:
            model: OpenAI model to use (default: gpt-4o-mini)
        """
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate text using OpenAI API.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "openai"
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model

