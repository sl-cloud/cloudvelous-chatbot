"""Tests for workflow learner utilities."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import List
from unittest.mock import MagicMock

import pytest

from app.models.training_sessions import TrainingSession
from app.models.workflow_vectors import WorkflowVector
from app.schemas.workflow import ReasoningChain, RetrievedChunkTrace, WorkflowStep
from app.services import workflow_learner as learner_module
from tests.conftest import StubDBSession


@pytest.fixture(autouse=True)
def reset_workflow_learner_singleton() -> None:
    learner_module._learner_instance = None


class _StubEmbedder:
    def embed_text(self, text: str) -> List[float]:
        # Deterministic embedding for test assertions
        return [float(len(text)), 1.0, 2.0]


def test_generate_reasoning_summary_lists_repositories(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reasoning summary should group retrieved chunks by repository."""
    monkeypatch.setattr(learner_module, "get_embedder", lambda: _StubEmbedder())
    learner = learner_module.WorkflowLearner()

    reasoning_chain = ReasoningChain(
        query="How do I deploy?",
        query_embedding_time_ms=10.0,
        retrieval_time_ms=20.0,
        generation_time_ms=30.0,
        total_time_ms=70.0,
        steps=[
            WorkflowStep(
                step_name="retrieval",
                timestamp=datetime.utcnow(),
                duration_ms=20.0,
                metadata={},
            )
        ],
        retrieved_chunks=[
            RetrievedChunkTrace(
                chunk_id=1,
                repo_name="repo-alpha",
                file_path="docs/setup.md",
                section_title=None,
                content_preview="...",
                similarity_score=0.9,
                rank_position=1,
                accuracy_weight=1.0,
            ),
            RetrievedChunkTrace(
                chunk_id=2,
                repo_name="repo-alpha",
                file_path="docs/config.md",
                section_title=None,
                content_preview="...",
                similarity_score=0.8,
                rank_position=2,
                accuracy_weight=1.0,
            ),
            RetrievedChunkTrace(
                chunk_id=3,
                repo_name="repo-beta",
                file_path="README.md",
                section_title=None,
                content_preview="...",
                similarity_score=0.85,
                rank_position=3,
                accuracy_weight=1.0,
            ),
        ],
        workflow_context=None,
        llm_provider="stub-provider",
        llm_model="stub-model",
    )

    summary = learner.generate_reasoning_summary(SimpleNamespace(), reasoning_chain)

    assert "repo-alpha" in summary
    assert "repo-beta" in summary
    assert "Total time" in summary


def test_create_workflow_embedding_persists_vector(monkeypatch: pytest.MonkeyPatch) -> None:
    """Workflow embeddings should be stored with generated summaries."""
    monkeypatch.setattr(learner_module, "get_embedder", lambda: _StubEmbedder())
    learner = learner_module.WorkflowLearner()

    chain = ReasoningChain(
        query="Deploy?",
        query_embedding_time_ms=5.0,
        retrieval_time_ms=10.0,
        generation_time_ms=15.0,
        total_time_ms=30.0,
        steps=[],
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="stub-provider",
        llm_model="stub-model",
    )

    session = TrainingSession(
        query="Deploy?",
        response="Use docker-compose",
        reasoning_chain=chain.model_dump(),
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="stub-provider",
        llm_model="stub-model",
        generation_time_ms=30.0,
        has_feedback=0,
        is_correct=None,
    )
    session.id = 1

    db = StubDBSession()
    db.add_query_result(TrainingSession, [session])

    result = learner.create_workflow_embedding(db=db, session_id=1, is_successful=True, confidence=0.8)

    assert result is not None
    assert db.committed is True
    assert result.reasoning_summary.startswith("Query: Deploy?")
    assert result.confidence_score == 0.8


def test_find_similar_workflows_returns_vectors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vector similarity query should return the underlying WorkflowVector objects."""
    monkeypatch.setattr(learner_module, "get_embedder", lambda: _StubEmbedder())
    learner = learner_module.WorkflowLearner()

    wf_one = WorkflowVector(session_id=1, reasoning_summary="a", workflow_embedding=[0.1], is_successful=1, confidence_score=1.0)
    wf_two = WorkflowVector(session_id=2, reasoning_summary="b", workflow_embedding=[0.2], is_successful=1, confidence_score=0.9)
    
    db = MagicMock()
    # The query chain needs to support chaining with filters
    query_chain = MagicMock()
    db.query.return_value = query_chain
    query_chain.filter.return_value = query_chain
    query_chain.order_by.return_value = query_chain
    query_chain.limit.return_value = query_chain
    # Return tuples of (WorkflowVector, distance) as the query does in real code
    query_chain.all.return_value = [(wf_one, 0.1), (wf_two, 0.2)]

    results = learner.find_similar_workflows(
        db=db,
        query_embedding=[0.1, 0.2, 0.3],
        top_k=2,
        min_similarity=0.5,
        successful_only=True,
    )

    assert results == [wf_one, wf_two]
    assert db.query.called


def test_get_successful_chunk_ids_deduplicates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Chunk IDs should be deduplicated and ignore explicitly negative feedback."""
    monkeypatch.setattr(learner_module, "get_embedder", lambda: _StubEmbedder())
    learner = learner_module.WorkflowLearner()

    db = MagicMock()
    all_mock = db.query.return_value.filter.return_value.all
    all_mock.side_effect = [
        [SimpleNamespace(chunk_id=1, was_useful=True), SimpleNamespace(chunk_id=2, was_useful=None)],
        [SimpleNamespace(chunk_id=2, was_useful=False), SimpleNamespace(chunk_id=3, was_useful=True)],
    ]

    workflow_vectors = [
        SimpleNamespace(session_id=1),
        SimpleNamespace(session_id=2),
    ]

    chunk_ids = learner.get_successful_chunk_ids(db=db, workflow_vectors=workflow_vectors)

    assert set(chunk_ids) == {1, 2, 3}
