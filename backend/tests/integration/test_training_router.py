"""
Integration tests for training feedback router endpoints.

Tests cover:
- Feedback submission and processing
- Chunk weight updates
- Workflow embedding creation
- Session retrieval with details
"""

from __future__ import annotations

from types import SimpleNamespace
from datetime import timedelta

import pytest

from app.main import app
from app.models import (
    get_db,
    TrainingSession,
    TrainingFeedback,
    EmbeddingLink,
    KnowledgeChunk,
)
from app.routers import training as training_router
from app.middleware.auth import create_access_token
from app.config import settings
from tests.conftest import StubDBSession


class _StubWorkflowLearner:
    def __init__(self) -> None:
        self.calls = []

    def create_workflow_embedding(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(id=11)


@pytest.fixture
def admin_token():
    """Create a valid admin JWT token for authentication."""
    return create_access_token(
        {"sub": "admin", "role": "admin"},
        expires_delta=timedelta(hours=1)
    )


def test_submit_feedback_updates_session_and_chunks(api_client, admin_token, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/train should record feedback, update weights, and invoke workflow learner."""
    db = StubDBSession()

    training_session = TrainingSession(
        query="Question?",
        response="Answer",
        reasoning_chain={},
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="stub",
        llm_model="stub-model",
        generation_time_ms=1.0,
        has_feedback=0,
        is_correct=None,
    )
    training_session.id = 1

    embedding_link = EmbeddingLink(
        session_id=1,
        chunk_id=5,
        similarity_score=0.9,
        rank_position=1,
        was_useful=None,
    )

    chunk = KnowledgeChunk(
        repo_name="repo",
        file_path="README.md",
        section_title=None,
        content="Content",
        embedding=[0.1],
        accuracy_weight=1.0,
    )
    chunk.id = 5

    db.add_query_result(TrainingSession, [training_session])
    db.add_query_result(EmbeddingLink, [embedding_link])
    db.add_query_result(KnowledgeChunk, [chunk])

    learner = _StubWorkflowLearner()
    monkeypatch.setattr(training_router, "get_workflow_learner", lambda: learner)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        response = api_client.post(
            "/api/train",
            json={
                "session_id": 1,
                "is_correct": True,
                "feedback_type": "correct",
                "chunk_feedback": [{"chunk_id": 5, "was_useful": True}],
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["chunks_updated"] == 1
    assert payload["workflow_embedding_created"] is True

    assert training_session.has_feedback == 1
    assert training_session.is_correct == 1
    assert embedding_link.was_useful is True
    assert chunk.accuracy_weight == pytest.approx(1.0 + settings.CHUNK_WEIGHT_ADJUSTMENT_RATE)

    added_types = {type(obj) for obj in db.added}
    assert TrainingFeedback in added_types
    assert len(learner.calls) == 1


def test_get_training_session_returns_chunk_details(api_client) -> None:
    """GET /api/session/{id} should return session metadata and retrieved chunks."""
    db = StubDBSession()

    training_session = TrainingSession(
        query="Question?",
        response="Answer",
        reasoning_chain={},
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="stub",
        llm_model="stub-model",
        generation_time_ms=1.0,
        has_feedback=1,
        is_correct=1,
    )
    training_session.id = 2
    training_session.created_at = "2024-01-01T00:00:00Z"  # type: ignore[attr-defined]

    embedding_link = EmbeddingLink(
        session_id=2,
        chunk_id=3,
        similarity_score=0.85,
        rank_position=1,
        was_useful=True,
    )

    chunk = KnowledgeChunk(
        repo_name="repo",
        file_path="guide.md",
        section_title="Guide",
        content="Chunk content",
        embedding=[0.2],
        accuracy_weight=1.2,
    )
    chunk.id = 3

    db.add_query_result(TrainingSession, [training_session])
    db.add_query_result((EmbeddingLink, KnowledgeChunk), [(embedding_link, chunk)])

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        response = api_client.get("/api/session/2")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    assert payload["session_id"] == 2
    assert payload["query"] == "Question?"
    assert payload["retrieved_chunks"][0]["chunk_id"] == 3
    assert payload["retrieved_chunks"][0]["file_path"] == "guide.md"

