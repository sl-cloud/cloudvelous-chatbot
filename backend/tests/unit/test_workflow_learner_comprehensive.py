"""Comprehensive tests for WorkflowLearner functionality."""

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
        # Return consistent embedding based on text length
        return [float(len(text)), 1.0, 2.0]


def test_get_workflow_learner_returns_singleton() -> None:
    """get_workflow_learner should return singleton instance."""
    learner_module._learner_instance = None
    
    first = learner_module.get_workflow_learner()
    second = learner_module.get_workflow_learner()
    
    assert first is second


def test_generate_reasoning_summary_empty_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reasoning summary should handle empty retrieved chunks."""
    monkeypatch.setattr(learner_module, "get_embedder", lambda: _StubEmbedder())
    learner = learner_module.WorkflowLearner()
    
    reasoning_chain = ReasoningChain(
        query="Test query?",
        query_embedding_time_ms=5.0,
        retrieval_time_ms=10.0,
        generation_time_ms=20.0,
        total_time_ms=35.0,
        steps=[],
        retrieved_chunks=[],  # Empty chunks
        workflow_context=None,
        llm_provider="test",
        llm_model="test-model",
    )
    
    summary = learner.generate_reasoning_summary(SimpleNamespace(), reasoning_chain)
    
    assert "Query: Test query?" in summary
    assert "Total time" in summary
    assert "Generated using test" in summary


def test_generate_reasoning_summary_single_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reasoning summary should handle single repository."""
    monkeypatch.setattr(learner_module, "get_embedder", lambda: _StubEmbedder())
    learner = learner_module.WorkflowLearner()
    
    reasoning_chain = ReasoningChain(
        query="Single repo query",
        query_embedding_time_ms=5.0,
        retrieval_time_ms=10.0,
        generation_time_ms=15.0,
        total_time_ms=30.0,
        steps=[],
        retrieved_chunks=[
            RetrievedChunkTrace(
                chunk_id=1,
                repo_name="single-repo",
                file_path="docs/readme.md",
                section_title=None,
                content_preview="Content...",
                similarity_score=0.95,
                rank_position=1,
                accuracy_weight=1.0,
            ),
            RetrievedChunkTrace(
                chunk_id=2,
                repo_name="single-repo",
                file_path="docs/guide.md",
                section_title="Setup",
                content_preview="Guide...",
                similarity_score=0.90,
                rank_position=2,
                accuracy_weight=1.0,
            ),
        ],
        workflow_context=None,
        llm_provider="test",
        llm_model="test-model",
    )
    
    summary = learner.generate_reasoning_summary(SimpleNamespace(), reasoning_chain)
    
    assert "single-repo" in summary
    assert "docs/readme.md" in summary
    assert "docs/guide.md" in summary


def test_create_workflow_embedding_unsuccessful_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Workflow embedding should be created for unsuccessful sessions too."""
    monkeypatch.setattr(learner_module, "get_embedder", lambda: _StubEmbedder())
    learner = learner_module.WorkflowLearner()
    
    chain = ReasoningChain(
        query="Failed query",
        query_embedding_time_ms=5.0,
        retrieval_time_ms=10.0,
        generation_time_ms=15.0,
        total_time_ms=30.0,
        steps=[],
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="test",
        llm_model="test",
    )
    
    session = TrainingSession(
        query="Failed query",
        response="Incorrect answer",
        reasoning_chain=chain.model_dump(),
        retrieved_chunks=[],
        workflow_context=None,
        llm_provider="test",
        llm_model="test",
        generation_time_ms=30.0,
        has_feedback=0,
        is_correct=None,
    )
    session.id = 1
    
    db = StubDBSession()
    db.add_query_result(TrainingSession, [session])
    
    result = learner.create_workflow_embedding(
        db=db,
        session_id=1,
        is_successful=False,  # Unsuccessful
        confidence=0.3
    )
    
    assert result is not None
    assert result.is_successful == 0
    assert result.confidence_score == 0.3


def test_find_similar_workflows_no_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """find_similar_workflows should handle case with no similar workflows."""
    monkeypatch.setattr(learner_module, "get_embedder", lambda: _StubEmbedder())
    learner = learner_module.WorkflowLearner()
    
    db = MagicMock()
    query_chain = MagicMock()
    db.query.return_value = query_chain
    query_chain.filter.return_value = query_chain
    query_chain.order_by.return_value = query_chain
    query_chain.limit.return_value = query_chain
    query_chain.all.return_value = []  # No results
    
    results = learner.find_similar_workflows(
        db=db,
        query_embedding=[0.1, 0.2, 0.3],
        top_k=5,
        min_similarity=0.7,
        successful_only=True,
    )
    
    assert results == []


def test_get_successful_chunk_ids_empty_workflows(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_successful_chunk_ids should handle empty workflow list."""
    monkeypatch.setattr(learner_module, "get_embedder", lambda: _StubEmbedder())
    learner = learner_module.WorkflowLearner()
    
    db = MagicMock()
    
    chunk_ids = learner.get_successful_chunk_ids(
        db=db,
        workflow_vectors=[]  # Empty list
    )
    
    assert chunk_ids == []


def test_get_successful_chunk_ids_filters_not_useful(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_successful_chunk_ids should filter out chunks marked as not useful."""
    monkeypatch.setattr(learner_module, "get_embedder", lambda: _StubEmbedder())
    learner = learner_module.WorkflowLearner()
    
    db = MagicMock()
    all_mock = db.query.return_value.filter.return_value.all
    
    # Return links where some are explicitly not useful
    all_mock.return_value = [
        SimpleNamespace(chunk_id=1, was_useful=True),
        SimpleNamespace(chunk_id=2, was_useful=False),  # Should be excluded
        SimpleNamespace(chunk_id=3, was_useful=None),   # Should be included
    ]
    
    workflow_vectors = [SimpleNamespace(session_id=1)]
    
    chunk_ids = learner.get_successful_chunk_ids(
        db=db,
        workflow_vectors=workflow_vectors
    )
    
    # Only chunks 1 and 3 should be included (2 is explicitly not useful)
    assert set(chunk_ids) == {1, 3}

