"""
Unit tests for embedding service.

Tests cover:
- Text embedding generation
- Model dimension exposure
- Cosine similarity calculation
- Singleton pattern enforcement
"""

from __future__ import annotations

import pytest

from app.services import embedder as embedder_module


@pytest.fixture(autouse=True)
def reset_embedder_singleton() -> None:
    """Ensure each test starts with a clean singleton."""
    embedder_module._embedder_instance = None


def test_embedding_service_provides_dimension() -> None:
    """Embedding service should expose model dimension via stubbed transformer."""
    service = embedder_module.EmbeddingService()

    assert service.dimension == service.model.get_sentence_embedding_dimension()


def test_embed_text_returns_list_of_floats() -> None:
    """Embedding service should return deterministic numeric vectors."""
    service = embedder_module.EmbeddingService()
    vector = service.embed_text("Cloudvelous intelligence")

    assert isinstance(vector, list)
    assert all(isinstance(value, float) for value in vector)


def test_get_embedder_returns_singleton_instance() -> None:
    """get_embedder should memoise a single EmbeddingService instance."""
    first = embedder_module.get_embedder()
    second = embedder_module.get_embedder()

    assert first is second


def test_cosine_similarity_matches_expected() -> None:
    """Cosine similarity helper should match the mathematical definition."""
    service = embedder_module.EmbeddingService()
    similarity = service.cosine_similarity([1, 0, 0], [1, 0, 0])
    assert pytest.approx(similarity, rel=1e-6) == 1.0

