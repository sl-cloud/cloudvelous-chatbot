"""Tests for retriever service edge cases and singleton behavior."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from app.services import retriever as retriever_module


class _StubEmbedder:
    def embed_text(self, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]


class _DummyQuery:
    """Minimal query stub replicating the chained SQLAlchemy API."""
    
    def __init__(self, results):
        self._results = list(results)
    
    def order_by(self, *_args, **_kwargs):
        return self
    
    def limit(self, *_args, **_kwargs):
        return self
    
    def all(self):
        return list(self._results)


class _DummyDB:
    def __init__(self, results):
        self._results = results
    
    def query(self, *_args, **_kwargs):
        return _DummyQuery(self._results)


@pytest.fixture(autouse=True)
def reset_retriever_singleton() -> None:
    retriever_module._retriever_instance = None


def _make_chunk(idx: int, weight: float) -> SimpleNamespace:
    return SimpleNamespace(
        id=idx,
        repo_name=f"repo-{idx}",
        file_path=f"path-{idx}.md",
        section_title=f"Section {idx}",
        content=f"Content {idx}",
        accuracy_weight=weight,
    )


def test_retriever_get_singleton() -> None:
    """get_retriever should return singleton instance."""
    retriever_module._retriever_instance = None
    
    first = retriever_module.get_retriever()
    second = retriever_module.get_retriever()
    
    assert first is second


def test_retrieve_uses_default_top_k(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retrieve should use settings.TOP_K_RETRIEVAL when top_k not specified."""
    monkeypatch.setattr(retriever_module, "get_embedder", lambda: _StubEmbedder())
    
    chunks = [_make_chunk(i, 1.0) for i in range(10)]
    query_results = [(chunk, 0.9 - i * 0.05) for i, chunk in enumerate(chunks)]
    
    db = _DummyDB(query_results)
    service = retriever_module.RetrieverService()
    
    # Don't specify top_k, should use default from settings
    results = service.retrieve(db=db, query="Test query")
    
    # Default TOP_K_RETRIEVAL is 5
    assert len(results) <= 5


def test_retrieve_by_embedding_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """retrieve_by_embedding should use default values when not specified."""
    monkeypatch.setattr(retriever_module, "get_embedder", lambda: _StubEmbedder())
    
    chunks = [_make_chunk(i, 1.0) for i in range(10)]
    query_results = [(chunk, 0.9 - i * 0.05) for i, chunk in enumerate(chunks)]
    
    db = _DummyDB(query_results)
    service = retriever_module.RetrieverService()
    
    # Call without optional parameters
    results = service.retrieve_by_embedding(
        db=db,
        query_embedding=[0.1, 0.2, 0.3]
    )
    
    assert len(results) <= 5
    assert all(isinstance(r, retriever_module.RetrievalResult) for r in results)


def test_retrieval_result_to_dict() -> None:
    """RetrievalResult should convert to dictionary correctly."""
    chunk = _make_chunk(1, 1.5)
    result = retriever_module.RetrievalResult(
        chunk=chunk,
        similarity_score=0.95,
        rank_position=1
    )
    
    result_dict = result.to_dict()
    
    assert result_dict["chunk_id"] == 1
    assert result_dict["repo_name"] == "repo-1"
    assert result_dict["file_path"] == "path-1.md"
    assert result_dict["section_title"] == "Section 1"
    assert result_dict["content"] == "Content 1"
    assert result_dict["similarity_score"] == 0.95
    assert result_dict["rank_position"] == 1
    assert result_dict["accuracy_weight"] == 1.5

