"""Basic smoke tests for SQLAlchemy model representations."""

from __future__ import annotations

from app.models.embedding_links import EmbeddingLink
from app.models.embeddings import KnowledgeChunk
from app.models.feedback import TrainingFeedback
from app.models.questions import ApprovedQuestion
from app.models.training_sessions import TrainingSession
from app.models.workflow_vectors import WorkflowVector


def test_training_session_repr_includes_id_and_query() -> None:
    session = TrainingSession(
        query="How do I deploy?",
        response="Use docker-compose",
        reasoning_chain={},
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="stub",
        llm_model="stub-model",
        generation_time_ms=10.0,
        has_feedback=0,
        is_correct=None,
    )
    session.id = 42

    repr_str = repr(session)
    assert "TrainingSession" in repr_str
    assert "42" in repr_str


def test_embedding_link_repr_includes_ids() -> None:
    link = EmbeddingLink(
        session_id=1,
        chunk_id=2,
        similarity_score=0.9,
        rank_position=1,
        was_useful=None,
    )
    repr_str = repr(link)
    assert "session_id=1" in repr_str
    assert "chunk_id=2" in repr_str


def test_knowledge_chunk_repr_includes_repo_and_file() -> None:
    chunk = KnowledgeChunk(
        repo_name="repo",
        file_path="README.md",
        section_title=None,
        content="Content",
        embedding=[0.1, 0.2],
        accuracy_weight=1.0,
    )
    repr_str = repr(chunk)
    assert "repo=repo" in repr_str
    assert "file=README.md" in repr_str


def test_workflow_vector_repr_includes_session_id() -> None:
    vector = WorkflowVector(
        session_id=5,
        reasoning_summary="Summary",
        workflow_embedding=[0.1, 0.2],
        is_successful=1,
        confidence_score=0.9,
    )
    repr_str = repr(vector)
    assert "session_id=5" in repr_str


def test_training_feedback_repr_contains_session_id() -> None:
    feedback = TrainingFeedback(
        session_id=9,
        feedback_type="correct",
        is_correct=True,
        user_correction=None,
        notes=None,
    )
    repr_str = repr(feedback)
    assert "session_id=9" in repr_str


def test_approved_question_repr_shortens_question() -> None:
    question = ApprovedQuestion(
        question="What is Cloudvelous?",
        category="general",
        embedding=[0.1, 0.2],
        is_active=True,
    )
    repr_str = repr(question)
    assert "Cloudvelous" in repr_str

