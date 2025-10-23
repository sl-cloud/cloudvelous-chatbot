"""Integration tests for the chat router endpoints."""

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
        return [0.1, 0.2, 0.3]


class _StubRetriever:
    def __init__(self, results):
        self.results = results

    def retrieve_by_embedding(self, **kwargs):
        return self.results


class _StubWorkflowLearner:
    def find_similar_workflows(self, **kwargs):
        return [SimpleNamespace(session_id=99)]

    def get_successful_chunk_ids(self, **kwargs):
        return [7]


class _StubLLMProvider:
    def generate(self, **kwargs):
        return "Stub answer"

    def get_provider_name(self):
        return "stub-llm"

    def get_model_name(self):
        return "stub-model"


def test_chat_endpoint_returns_answer_and_trace(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/ask should execute the chat workflow and persist a training session."""
    db = StubDBSession()

    chunk = SimpleNamespace(
        id=7,
        repo_name="cloudvelous",
        file_path="README.md",
        section_title="Intro",
        content="Cloudvelous overview content.",
        accuracy_weight=1.0,
    )
    retrieval_results = [RetrievalResult(chunk=chunk, similarity_score=0.95, rank_position=1)]

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
            json={"question": "What is Cloudvelous?", "include_trace": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    assert payload["answer"] == "Stub answer"
    assert payload["session_id"] == 1
    assert payload["sources"] == ["cloudvelous/README.md"]
    assert payload["reasoning_chain"]["query"] == "What is Cloudvelous?"

    # Verify persistence interactions captured by stub session
    added_types = {type(obj) for obj in db.added}
    assert TrainingSession in added_types
    assert EmbeddingLink in added_types
