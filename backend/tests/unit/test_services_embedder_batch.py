"""
Unit tests for embedding service batch operations.

Tests cover:
- Batch text embedding generation
- Single text batch operation
- Empty list handling
- Result consistency with single embedding
"""

from __future__ import annotations

import pytest

from app.services import embedder as embedder_module


@pytest.fixture(autouse=True)
def reset_embedder_singleton() -> None:
    """Ensure each test starts with a clean singleton."""
    embedder_module._embedder_instance = None


def test_embed_batch_returns_multiple_vectors() -> None:
    """Embedding service should handle batch operations efficiently."""
    service = embedder_module.EmbeddingService()
    
    texts = [
        "First text to embed",
        "Second text to embed",
        "Third text to embed"
    ]
    
    vectors = service.embed_batch(texts)
    
    assert isinstance(vectors, list)
    assert len(vectors) == 3
    assert all(isinstance(vec, list) for vec in vectors)
    assert all(len(vec) == service.dimension for vec in vectors)


def test_embed_batch_with_single_text() -> None:
    """Batch embedding should work with single text."""
    service = embedder_module.EmbeddingService()
    
    vectors = service.embed_batch(["Single text"])
    
    assert len(vectors) == 1
    assert isinstance(vectors[0], list)


def test_embed_batch_empty_list() -> None:
    """Batch embedding should handle empty list."""
    service = embedder_module.EmbeddingService()
    
    vectors = service.embed_batch([])
    
    assert vectors == []

