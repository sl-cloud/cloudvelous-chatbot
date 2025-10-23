"""
Unit tests for retrieval service.

Tests cover:
- Accuracy weight application
- Workflow-based chunk boosting
- Result ranking and ordering
- Integration with embedder service
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import List, Sequence

import pytest

from app.services import retriever as retriever_module


class _DummyQuery:
    """Minimal query stub replicating the chained SQLAlchemy API."""

    def __init__(self, results: Sequence) -> None:
        self._results = list(results)

    def order_by(self, *_args, **_kwargs) -> "_DummyQuery":
        return self

    def limit(self, *_args, **_kwargs) -> "_DummyQuery":
        return self

    def all(self) -> List:
        return list(self._results)


class _DummyDB:
    def __init__(self, results: Sequence) -> None:
        self._results = results

    def query(self, *_args, **_kwargs) -> _DummyQuery:  # type: ignore[override]
        return _DummyQuery(self._results)


class _StubEmbedder:
    def embed_text(self, text: str) -> List[float]:  # pragma: no cover - trivial
        return [0.1, 0.2, 0.3]


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


def test_retrieve_by_embedding_applies_accuracy_weights(monkeypatch: pytest.MonkeyPatch) -> None:
    """Chunks with higher accuracy_weight should outrank more similar chunks."""
    chunk_one = _make_chunk(1, weight=1.0)
    chunk_two = _make_chunk(2, weight=1.5)

    # Similarity scores before weighting (higher is better)
    query_results = [
        (chunk_one, 0.92),
        (chunk_two, 0.88),
    ]

    db = _DummyDB(query_results)
    service = retriever_module.RetrieverService()
    service.embedder = _StubEmbedder()  # type: ignore[attr-defined]

    results = service.retrieve_by_embedding(
        db=db,
        query_embedding=[0.1, 0.2, 0.3],
        top_k=2,
    )

    assert [result.chunk.id for result in results] == [2, 1]
    assert results[0].rank_position == 1
    assert results[1].rank_position == 2


def test_retrieve_with_boost_prioritises_specified_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Boosted chunk IDs should get multiplied by boost_factor."""
    monkeypatch.setattr(retriever_module, "get_embedder", lambda: _StubEmbedder())

    chunk_one = _make_chunk(1, weight=1.0)
    chunk_two = _make_chunk(2, weight=1.0)

    query_results = [
        (chunk_one, 0.95),
        (chunk_two, 0.90),
    ]

    db = _DummyDB(query_results)
    service = retriever_module.RetrieverService()

    results = service.retrieve(
        db=db,
        query="How do I deploy?",
        top_k=2,
        boost_chunk_ids=[2],
        boost_factor=2.0,
    )

    assert [result.chunk.id for result in results] == [2, 1]

