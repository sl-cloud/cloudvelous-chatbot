"""
Unit tests for answer generation service.

Tests cover:
- Context building from retrieval results
- Prompt construction
- LLM provider integration
- Provider metadata exposure
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

from app.services.generator import GeneratorService
from app.services.retriever import RetrievalResult


class _FakeChunk:
    def __init__(self, idx: int) -> None:
        self.id = idx
        self.repo_name = f"repo-{idx}"
        self.file_path = f"docs/file-{idx}.md"
        self.section_title = f"Section {idx}"
        self.content = f"Chunk content {idx}"
        self.accuracy_weight = 1.0


class _FakeProvider:
    def __init__(self) -> None:
        self.calls: List[dict] = []

    def generate(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return "Generated answer"

    def get_provider_name(self) -> str:
        return "stub-provider"

    def get_model_name(self) -> str:
        return "stub-model"


def _make_retrieval_results(count: int) -> List[RetrievalResult]:
    results: List[RetrievalResult] = []
    for idx in range(1, count + 1):
        chunk = _FakeChunk(idx)
        result = RetrievalResult(chunk=chunk, similarity_score=0.9, rank_position=idx)
        results.append(result)
    return results


def test_generator_builds_context_and_invokes_provider() -> None:
    """Generator service should build prompts and delegate to provider."""
    provider = _FakeProvider()
    service = GeneratorService(provider)

    retrieval_results = _make_retrieval_results(2)
    answer = service.generate_answer(
        query="How do I deploy?",
        retrieval_results=retrieval_results,
        temperature=0.5,
        max_tokens=200,
    )

    assert answer == "Generated answer"
    assert len(provider.calls) == 1

    call = provider.calls[0]
    assert "Context from repositories" in call["prompt"]
    assert call["system_prompt"].startswith("You are Cloudvelous Chat Assistant")
    assert call["temperature"] == 0.5
    assert call["max_tokens"] == 200


def test_generator_exposes_provider_metadata() -> None:
    """Provider metadata should be accessible for logging and tracing."""
    provider = _FakeProvider()
    service = GeneratorService(provider)

    assert service.get_provider_name() == "stub-provider"
    assert service.get_model_name() == "stub-model"

