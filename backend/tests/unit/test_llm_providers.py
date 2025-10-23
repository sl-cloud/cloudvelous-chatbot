"""Tests for LLM provider implementations."""

from __future__ import annotations

from app.llm.openai_provider import OpenAIProvider
from app.llm.gemini_provider import GeminiProvider


def test_openai_provider_generates_with_system_prompt() -> None:
    """OpenAI provider should use system prompts when provided."""
    provider = OpenAIProvider()
    
    response = provider.generate(
        prompt="What is AI?",
        system_prompt="You are a helpful assistant.",
        temperature=0.5,
        max_tokens=100
    )
    
    assert isinstance(response, str)
    assert len(response) > 0


def test_openai_provider_generates_without_system_prompt() -> None:
    """OpenAI provider should work without system prompts."""
    provider = OpenAIProvider()
    
    response = provider.generate(
        prompt="What is AI?",
        temperature=0.5,
        max_tokens=100
    )
    
    assert isinstance(response, str)
    assert len(response) > 0


def test_openai_provider_metadata() -> None:
    """OpenAI provider should expose correct metadata."""
    provider = OpenAIProvider(model="gpt-4")
    
    assert provider.get_provider_name() == "openai"
    assert provider.get_model_name() == "gpt-4"


def test_gemini_provider_generates_with_system_prompt() -> None:
    """Gemini provider should combine system and user prompts."""
    provider = GeminiProvider()
    
    response = provider.generate(
        prompt="What is AI?",
        system_prompt="You are a helpful assistant.",
        temperature=0.7,
        max_tokens=200
    )
    
    assert isinstance(response, str)
    assert len(response) > 0


def test_gemini_provider_generates_without_system_prompt() -> None:
    """Gemini provider should work without system prompts."""
    provider = GeminiProvider()
    
    response = provider.generate(
        prompt="What is AI?",
        temperature=0.7,
        max_tokens=200
    )
    
    assert isinstance(response, str)
    assert len(response) > 0


def test_gemini_provider_metadata() -> None:
    """Gemini provider should expose correct metadata."""
    provider = GeminiProvider(model="gemini-pro")
    
    assert provider.get_provider_name() == "gemini"
    assert provider.get_model_name() == "gemini-pro"

