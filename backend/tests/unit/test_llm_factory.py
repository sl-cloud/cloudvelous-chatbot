"""Tests for the LLM provider factory and singleton behaviour."""

from __future__ import annotations

import pytest

from app.llm.factory import LLMProviderFactory, get_llm_provider
from app.llm.gemini_provider import GeminiProvider
from app.llm.openai_provider import OpenAIProvider


@pytest.fixture(autouse=True)
def reset_llm_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.llm.factory._provider_instance", None)


def test_factory_creates_openai_provider() -> None:
    provider = LLMProviderFactory.create_provider("openai")
    assert isinstance(provider, OpenAIProvider)
    assert provider.get_provider_name() == "openai"


def test_factory_creates_gemini_provider() -> None:
    provider = LLMProviderFactory.create_provider("gemini")
    assert isinstance(provider, GeminiProvider)
    assert provider.get_provider_name() == "gemini"


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError):
        LLMProviderFactory.create_provider("anthropic")


def test_get_llm_provider_returns_singleton() -> None:
    first = get_llm_provider()
    second = get_llm_provider()
    assert first is second
