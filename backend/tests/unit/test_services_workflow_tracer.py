"""Tests for WorkflowTracer capturing reasoning chain details."""

from __future__ import annotations

import time

from app.services.workflow_tracer import WorkflowTracer


def test_workflow_tracer_records_steps_and_chunks() -> None:
    """Workflow tracer should capture steps, retrieved chunks, and metadata."""
    tracer = WorkflowTracer("What is Cloudvelous?")

    start = tracer.start_step("query_embedding")
    time.sleep(0.001)  # ensure non-zero duration
    tracer.end_step("query_embedding", start, {"dimension": 8})

    tracer.add_retrieved_chunk(
        chunk_id=1,
        repo_name="repo",
        file_path="README.md",
        section_title="Intro",
        content="A" * 210,
        similarity_score=0.9,
        rank_position=1,
        accuracy_weight=1.0,
    )

    tracer.set_llm_info(provider="stub-provider", model="stub-model")
    chain = tracer.build_reasoning_chain()

    assert chain.query == "What is Cloudvelous?"
    assert len(chain.steps) == 1
    assert chain.steps[0].step_name == "query_embedding"
    assert len(chain.retrieved_chunks) == 1
    assert chain.retrieved_chunks[0].content_preview.endswith("...")
    assert chain.llm_provider == "stub-provider"
    assert chain.total_time_ms >= chain.query_embedding_time_ms

