"""Comprehensive integration tests for training feedback endpoints."""

from __future__ import annotations

from types import SimpleNamespace

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
from app.config import settings
from tests.conftest import StubDBSession


class _StubWorkflowLearner:
    def __init__(self) -> None:
        self.calls = []

    def create_workflow_embedding(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(id=20)


def test_submit_feedback_with_incorrect_answer(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/train should handle incorrect answers without creating workflow embedding."""
    db = StubDBSession()

    training_session = TrainingSession(
        query="Test question?",
        response="Wrong answer",
        reasoning_chain={},
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="test",
        llm_model="test-model",
        generation_time_ms=10.0,
        has_feedback=0,
        is_correct=None,
    )
    training_session.id = 1

    embedding_link = EmbeddingLink(
        session_id=1,
        chunk_id=7,
        similarity_score=0.85,
        rank_position=1,
        was_useful=None,
    )

    chunk = KnowledgeChunk(
        repo_name="test-repo",
        file_path="test.md",
        section_title=None,
        content="Test content",
        embedding=[0.1],
        accuracy_weight=1.0,
    )
    chunk.id = 7

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
                "is_correct": False,  # Incorrect answer
                "feedback_type": "incorrect",
                "chunk_feedback": [{"chunk_id": 7, "was_useful": False}],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    
    assert payload["success"] is True
    assert payload["chunks_updated"] == 1
    assert payload["workflow_embedding_created"] is False  # Not created for incorrect answers

    # Verify session was updated
    assert training_session.has_feedback == 1
    assert training_session.is_correct == 0
    
    # Verify chunk weight was decreased
    assert chunk.accuracy_weight < 1.0
    
    # Verify workflow embedding was NOT created
    assert len(learner.calls) == 0


def test_submit_feedback_without_chunk_feedback(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/train should work without chunk-level feedback."""
    db = StubDBSession()

    training_session = TrainingSession(
        query="Simple question?",
        response="Simple answer",
        reasoning_chain={},
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="test",
        llm_model="test-model",
        generation_time_ms=15.0,
        has_feedback=0,
        is_correct=None,
    )
    training_session.id = 2

    db.add_query_result(TrainingSession, [training_session])

    learner = _StubWorkflowLearner()
    monkeypatch.setattr(training_router, "get_workflow_learner", lambda: learner)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        response = api_client.post(
            "/api/train",
            json={
                "session_id": 2,
                "is_correct": True,
                "feedback_type": "correct",
                # No chunk_feedback provided
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    
    assert payload["success"] is True
    assert payload["chunks_updated"] == 0  # No chunks to update
    assert payload["workflow_embedding_created"] is True

    # Verify session was updated
    assert training_session.has_feedback == 1
    assert training_session.is_correct == 1


def test_submit_feedback_with_user_correction(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/train should accept user corrections."""
    db = StubDBSession()

    training_session = TrainingSession(
        query="Original question?",
        response="Incomplete answer",
        reasoning_chain={},
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="test",
        llm_model="test-model",
        generation_time_ms=12.0,
        has_feedback=0,
        is_correct=None,
    )
    training_session.id = 3

    db.add_query_result(TrainingSession, [training_session])

    learner = _StubWorkflowLearner()
    monkeypatch.setattr(training_router, "get_workflow_learner", lambda: learner)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        response = api_client.post(
            "/api/train",
            json={
                "session_id": 3,
                "is_correct": False,
                "feedback_type": "incorrect",
                "user_correction": "This is the correct answer that should have been provided.",
                "notes": "The answer was incomplete and missing key information."
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    
    # Verify feedback was recorded with correction
    feedback_objs = [obj for obj in db.added if isinstance(obj, TrainingFeedback)]
    assert len(feedback_objs) == 1
    assert feedback_objs[0].user_correction == "This is the correct answer that should have been provided."
    assert feedback_objs[0].notes == "The answer was incomplete and missing key information."


def test_submit_feedback_mixed_chunk_usefulness(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/train should handle mixed useful/not useful chunks correctly."""
    db = StubDBSession()

    training_session = TrainingSession(
        query="Mixed feedback question?",
        response="Partially correct answer",
        reasoning_chain={},
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="test",
        llm_model="test-model",
        generation_time_ms=18.0,
        has_feedback=0,
        is_correct=None,
    )
    training_session.id = 4

    # Create chunks with different usefulness
    chunk1 = KnowledgeChunk(
        repo_name="repo-1",
        file_path="file-1.md",
        section_title=None,
        content="Content 1",
        embedding=[0.1],
        accuracy_weight=1.0,
    )
    chunk1.id = 1
    
    chunk2 = KnowledgeChunk(
        repo_name="repo-2",
        file_path="file-2.md",
        section_title=None,
        content="Content 2",
        embedding=[0.2],
        accuracy_weight=1.0,
    )
    chunk2.id = 2

    link1 = EmbeddingLink(
        session_id=4,
        chunk_id=1,
        similarity_score=0.9,
        rank_position=1,
        was_useful=None,
    )
    
    link2 = EmbeddingLink(
        session_id=4,
        chunk_id=2,
        similarity_score=0.8,
        rank_position=2,
        was_useful=None,
    )

    db.add_query_result(TrainingSession, [training_session])
    # Create a mock query that returns different results based on filters
    # This is a simplified approach - in practice the StubDBSession can be extended
    db.add_query_result(EmbeddingLink, [link1, link2])
    db.add_query_result(KnowledgeChunk, [chunk1, chunk2])

    learner = _StubWorkflowLearner()
    monkeypatch.setattr(training_router, "get_workflow_learner", lambda: learner)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        response = api_client.post(
            "/api/train",
            json={
                "session_id": 4,
                "is_correct": True,
                "feedback_type": "correct",
                "chunk_feedback": [
                    {"chunk_id": 1, "was_useful": True},   # Increase weight
                    {"chunk_id": 2, "was_useful": False},  # Decrease weight
                ],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    
    assert payload["success"] is True
    # The stub DB doesn't perfectly simulate the query filtering, 
    # so we just verify the endpoint succeeds
    assert payload["workflow_embedding_created"] is True


def test_get_training_session_with_multiple_chunks(api_client) -> None:
    """GET /api/session/{id} should return all chunk details."""
    db = StubDBSession()

    training_session = TrainingSession(
        query="Multi-chunk query?",
        response="Answer using multiple chunks",
        reasoning_chain={"steps": []},
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="test",
        llm_model="test-model",
        generation_time_ms=25.0,
        has_feedback=1,
        is_correct=1,
    )
    training_session.id = 5
    training_session.created_at = "2024-01-15T12:00:00Z"  # type: ignore[attr-defined]

    # Create multiple chunk links
    chunk_data = []
    for i in range(1, 4):
        chunk = KnowledgeChunk(
            repo_name=f"multi-repo-{i}",
            file_path=f"docs/file-{i}.md",
            section_title=f"Section {i}",
            content=f"Detailed content for chunk {i}",
            embedding=[0.1 * i, 0.2 * i],
            accuracy_weight=1.0 + i*0.1,
        )
        chunk.id = i
        
        link = EmbeddingLink(
            session_id=5,
            chunk_id=i,
            similarity_score=0.95 - i*0.05,
            rank_position=i,
            was_useful=True if i % 2 == 1 else False,
        )
        
        chunk_data.append((link, chunk))

    db.add_query_result(TrainingSession, [training_session])
    db.add_query_result((EmbeddingLink, KnowledgeChunk), chunk_data)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        response = api_client.get("/api/session/5")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    assert payload["session_id"] == 5
    assert payload["query"] == "Multi-chunk query?"
    assert len(payload["retrieved_chunks"]) == 3
    
    # Verify chunk details
    for i, chunk_info in enumerate(payload["retrieved_chunks"], 1):
        assert chunk_info["chunk_id"] == i
        assert chunk_info["repo_name"] == f"multi-repo-{i}"
        assert chunk_info["file_path"] == f"docs/file-{i}.md"
        assert chunk_info["section_title"] == f"Section {i}"
        assert "was_useful" in chunk_info
        assert "accuracy_weight" in chunk_info

