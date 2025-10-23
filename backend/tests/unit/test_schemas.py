"""Validation tests for Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.training import ChunkFeedback, TrainingFeedbackRequest
from app.schemas.workflow import ReasoningChain, RetrievedChunkTrace, WorkflowStep


def test_chat_request_requires_non_empty_question() -> None:
    """Empty questions should be rejected by validation."""
    with pytest.raises(ValidationError):
        ChatRequest(question="")


def test_chat_response_allows_optional_reasoning_chain() -> None:
    """Reasoning chain should be optional and omitted by default."""
    response = ChatResponse(answer="Answer", session_id=1, sources=["repo/file.md"])
    assert response.reasoning_chain is None


def test_training_feedback_request_accepts_chunk_feedback() -> None:
    """Chunk feedback should be parsed into Pydantic models."""
    request = TrainingFeedbackRequest(
        session_id=1,
        is_correct=True,
        feedback_type="correct",
        chunk_feedback=[{"chunk_id": 10, "was_useful": True}],
    )
    assert isinstance(request.chunk_feedback[0], ChunkFeedback)


def test_reasoning_chain_structure_serialises() -> None:
    """Reasoning chain should preserve lists of steps and retrieved chunks."""
    chain = ReasoningChain(
        query="Question",
        query_embedding_time_ms=10.0,
        retrieval_time_ms=20.0,
        generation_time_ms=30.0,
        total_time_ms=60.0,
        steps=[
            WorkflowStep(
                step_name="retrieval",
                timestamp=datetime.utcnow(),
                duration_ms=20.0,
                metadata={"count": 2},
            )
        ],
        retrieved_chunks=[
            RetrievedChunkTrace(
                chunk_id=1,
                repo_name="repo",
                file_path="README.md",
                section_title=None,
                content_preview="...",
                similarity_score=0.9,
                rank_position=1,
                accuracy_weight=1.0,
            )
        ],
        workflow_context=None,
        llm_provider="stub-provider",
        llm_model="stub-model",
    )

    dumped = chain.model_dump()
    assert dumped["query"] == "Question"
    assert len(dumped["steps"]) == 1
    assert dumped["retrieved_chunks"][0]["chunk_id"] == 1

