"""
Comprehensive integration tests for complete chat workflows.

Tests cover:
- Workflow learning disabled/enabled scenarios
- Multiple chunk retrieval handling
- Similar workflow boosting
- Timing information capture
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.main import app
from app.models import get_db, TrainingSession, EmbeddingLink
from app.routers import chat as chat_router
from app.services.retriever import RetrievalResult
from tests.conftest import StubDBSession


class _StubEmbedder:
    def embed_text(self, text: str):
        return [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]


class _StubRetriever:
    def __init__(self, results):
        self.results = results

    def retrieve_by_embedding(self, **kwargs):
        return self.results


class _StubWorkflowLearner:
    def find_similar_workflows(self, **kwargs):
        # Return empty list for no similar workflows
        return []

    def get_successful_chunk_ids(self, **kwargs):
        return []


class _StubLLMProvider:
    def generate(self, **kwargs):
        return "This is a comprehensive test answer."

    def get_provider_name(self):
        return "test-llm"

    def get_model_name(self):
        return "test-model-v1"


def test_chat_workflow_with_workflow_disabled(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """Chat workflow should work when workflow learning is disabled."""
    db = StubDBSession()

    chunk = SimpleNamespace(
        id=10,
        repo_name="test-repo",
        file_path="docs/test.md",
        section_title="Test Section",
        content="Test content for the chatbot.",
        accuracy_weight=1.0,
    )
    retrieval_results = [RetrievalResult(chunk=chunk, similarity_score=0.88, rank_position=1)]

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    monkeypatch.setattr(chat_router, "get_embedder", lambda: _StubEmbedder())
    monkeypatch.setattr(chat_router, "get_retriever", lambda: _StubRetriever(retrieval_results))
    monkeypatch.setattr(chat_router, "get_workflow_learner", lambda: _StubWorkflowLearner())
    monkeypatch.setattr(chat_router, "get_llm_provider", lambda: _StubLLMProvider())
    
    # Disable workflow embeddings
    monkeypatch.setattr("app.routers.chat.settings.WORKFLOW_EMBEDDING_ENABLED", False)

    try:
        response = api_client.post(
            "/api/ask",
            json={"question": "What is the test?", "include_trace": False},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    assert payload["answer"] == "This is a comprehensive test answer."
    assert payload["session_id"] == 1
    assert "sources" in payload
    assert payload.get("reasoning_chain") is None  # None when include_trace=False


def test_chat_workflow_with_multiple_chunks(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """Chat workflow should handle multiple retrieved chunks."""
    db = StubDBSession()

    # Create multiple chunks from different repos
    chunks = []
    for i in range(1, 6):
        chunk = SimpleNamespace(
            id=i,
            repo_name=f"repo-{i}",
            file_path=f"docs/file-{i}.md",
            section_title=f"Section {i}",
            content=f"Content from chunk {i}.",
            accuracy_weight=1.0,
        )
        chunks.append(chunk)
    
    retrieval_results = [
        RetrievalResult(chunk=chunk, similarity_score=0.95 - i*0.05, rank_position=i)
        for i, chunk in enumerate(chunks, 1)
    ]

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    monkeypatch.setattr(chat_router, "get_embedder", lambda: _StubEmbedder())
    monkeypatch.setattr(chat_router, "get_retriever", lambda: _StubRetriever(retrieval_results))
    monkeypatch.setattr(chat_router, "get_workflow_learner", lambda: _StubWorkflowLearner())
    monkeypatch.setattr(chat_router, "get_llm_provider", lambda: _StubLLMProvider())

    try:
        response = api_client.post(
            "/api/ask",
            json={"question": "Multi-chunk question?", "include_trace": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    # Verify multiple sources
    assert len(payload["sources"]) == 5
    
    # Verify reasoning chain includes all chunks
    assert len(payload["reasoning_chain"]["retrieved_chunks"]) == 5
    
    # Verify embedding links were created for all chunks
    embedding_links = [obj for obj in db.added if isinstance(obj, EmbeddingLink)]
    assert len(embedding_links) == 5


def test_chat_workflow_with_similar_workflows_found(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """Chat workflow should boost chunks when similar workflows are found."""
    db = StubDBSession()

    chunk1 = SimpleNamespace(
        id=1,
        repo_name="primary-repo",
        file_path="guide.md",
        section_title="Guide",
        content="Primary content.",
        accuracy_weight=1.0,
    )
    chunk2 = SimpleNamespace(
        id=2,
        repo_name="secondary-repo",
        file_path="readme.md",
        section_title=None,
        content="Secondary content.",
        accuracy_weight=1.0,
    )
    
    retrieval_results = [
        RetrievalResult(chunk=chunk1, similarity_score=0.92, rank_position=1),
        RetrievalResult(chunk=chunk2, similarity_score=0.85, rank_position=2),
    ]

    class _WorkflowLearnerWithResults:
        def find_similar_workflows(self, **kwargs):
            # Return some similar workflows
            return [
                SimpleNamespace(session_id=101),
                SimpleNamespace(session_id=102),
            ]

        def get_successful_chunk_ids(self, **kwargs):
            # Return chunk IDs to boost
            return [1, 3]  # Boost chunk 1

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    monkeypatch.setattr(chat_router, "get_embedder", lambda: _StubEmbedder())
    monkeypatch.setattr(chat_router, "get_retriever", lambda: _StubRetriever(retrieval_results))
    monkeypatch.setattr(chat_router, "get_workflow_learner", lambda: _WorkflowLearnerWithResults())
    monkeypatch.setattr(chat_router, "get_llm_provider", lambda: _StubLLMProvider())
    monkeypatch.setattr("app.routers.chat.settings.WORKFLOW_EMBEDDING_ENABLED", True)

    try:
        response = api_client.post(
            "/api/ask",
            json={"question": "Question with workflow context?", "include_trace": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    # Verify workflow search was performed
    reasoning = payload["reasoning_chain"]
    workflow_step = next((s for s in reasoning["steps"] if s["step_name"] == "workflow_search"), None)
    assert workflow_step is not None


def test_chat_workflow_includes_timing_information(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """Chat workflow should include accurate timing information."""
    db = StubDBSession()

    chunk = SimpleNamespace(
        id=1,
        repo_name="timing-repo",
        file_path="timing.md",
        section_title=None,
        content="Timing test content.",
        accuracy_weight=1.0,
    )
    retrieval_results = [RetrievalResult(chunk=chunk, similarity_score=0.9, rank_position=1)]

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    monkeypatch.setattr(chat_router, "get_embedder", lambda: _StubEmbedder())
    monkeypatch.setattr(chat_router, "get_retriever", lambda: _StubRetriever(retrieval_results))
    monkeypatch.setattr(chat_router, "get_workflow_learner", lambda: _StubWorkflowLearner())
    monkeypatch.setattr(chat_router, "get_llm_provider", lambda: _StubLLMProvider())

    try:
        response = api_client.post(
            "/api/ask",
            json={"question": "Timing test?", "include_trace": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    reasoning = payload["reasoning_chain"]
    
    # Verify timing fields exist and are reasonable
    assert reasoning["query_embedding_time_ms"] >= 0
    assert reasoning["retrieval_time_ms"] >= 0
    assert reasoning["generation_time_ms"] >= 0
    assert reasoning["total_time_ms"] >= 0
    
    # Total should be sum of parts
    assert reasoning["total_time_ms"] >= reasoning["query_embedding_time_ms"]
    assert reasoning["total_time_ms"] >= reasoning["retrieval_time_ms"]
    assert reasoning["total_time_ms"] >= reasoning["generation_time_ms"]

