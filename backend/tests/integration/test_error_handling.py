"""
Integration tests for error handling across API routers.

Tests cover:
- Embedding service failures
- Missing session handling
- Database connection errors
- Graceful error responses
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.main import app
from app.models import get_db
from app.routers import chat as chat_router
from tests.conftest import StubDBSession


class _FailingEmbedder:
    """Embedder that raises an exception."""
    def embed_text(self, text: str):
        raise RuntimeError("Embedding service failed")


class _FailingLLMProvider:
    """LLM provider that raises an exception."""
    def generate(self, **kwargs):
        raise RuntimeError("LLM generation failed")
    
    def get_provider_name(self):
        return "failing-llm"
    
    def get_model_name(self):
        return "failing-model"


def test_chat_endpoint_handles_embedding_failure(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/ask should handle embedding service failures gracefully."""
    db = StubDBSession()
    
    def override_db():
        yield db
    
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(chat_router, "get_embedder", lambda: _FailingEmbedder())
    
    try:
        response = api_client.post(
            "/api/ask",
            json={"question": "Test question?", "include_trace": False},
        )
    finally:
        app.dependency_overrides.clear()
    
    assert response.status_code == 500
    assert "Error processing question" in response.json()["detail"]


def test_training_endpoint_handles_missing_session(api_client) -> None:
    """POST /api/train should return 404 for non-existent sessions."""
    db = StubDBSession()
    db.add_query_result(None, [])  # No training session found
    
    def override_db():
        yield db
    
    app.dependency_overrides[get_db] = override_db
    
    try:
        response = api_client.post(
            "/api/train",
            json={
                "session_id": 999,
                "is_correct": True,
                "feedback_type": "correct",
            },
        )
    finally:
        app.dependency_overrides.clear()
    
    assert response.status_code == 404
    assert "Training session not found" in response.json()["detail"]


def test_get_session_handles_missing_session(api_client) -> None:
    """GET /api/session/{id} should return 404 for non-existent sessions."""
    db = StubDBSession()
    db.add_query_result(None, [])  # No training session found
    
    def override_db():
        yield db
    
    app.dependency_overrides[get_db] = override_db
    
    try:
        response = api_client.get("/api/session/999")
    finally:
        app.dependency_overrides.clear()
    
    assert response.status_code == 404
    assert "Training session not found" in response.json()["detail"]

