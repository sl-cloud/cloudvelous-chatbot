"""
Google Gemini LLM provider implementation.
"""

from typing import Optional
import google.generativeai as genai

from app.llm.base import ILLMProvider
from app.config import settings


class GeminiProvider(ILLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini provider.
        
        Args:
            model: Gemini model to use (default: gemini-1.5-flash)
        """
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate text using Gemini API.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        
        response = self.model.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        return response.text
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "gemini"
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model_name

