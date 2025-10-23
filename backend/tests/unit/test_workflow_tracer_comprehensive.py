"""Comprehensive tests for WorkflowTracer functionality."""

from __future__ import annotations

import time

from app.services.workflow_tracer import WorkflowTracer


def test_workflow_tracer_multiple_steps() -> None:
    """Workflow tracer should handle multiple workflow steps."""
    tracer = WorkflowTracer("Complex query with multiple steps")
    
    # Step 1: Embedding
    start1 = tracer.start_step("query_embedding")
    time.sleep(0.001)
    tracer.end_step("query_embedding", start1, {"dimension": 384})
    
    # Step 2: Workflow search
    start2 = tracer.start_step("workflow_search")
    time.sleep(0.001)
    tracer.end_step("workflow_search", start2, {"found": 3})
    
    # Step 3: Retrieval
    start3 = tracer.start_step("retrieval")
    time.sleep(0.001)
    tracer.end_step("retrieval", start3, {"chunks": 5})
    
    # Step 4: Generation
    start4 = tracer.start_step("generation")
    time.sleep(0.001)
    tracer.end_step("generation", start4, {"tokens": 150})
    
    tracer.set_llm_info(provider="test-provider", model="test-model")
    chain = tracer.build_reasoning_chain()
    
    assert len(chain.steps) == 4
    assert chain.steps[0].step_name == "query_embedding"
    assert chain.steps[1].step_name == "workflow_search"
    assert chain.steps[2].step_name == "retrieval"
    assert chain.steps[3].step_name == "generation"
    
    # Verify timing accumulation
    assert chain.total_time_ms > 0
    assert chain.query_embedding_time_ms > 0


def test_workflow_tracer_multiple_chunks() -> None:
    """Workflow tracer should handle multiple retrieved chunks."""
    tracer = WorkflowTracer("What is the deployment process?")
    
    # Add multiple chunks
    for i in range(1, 6):
        tracer.add_retrieved_chunk(
            chunk_id=i,
            repo_name=f"repo-{i}",
            file_path=f"docs/file-{i}.md",
            section_title=f"Section {i}",
            content=f"Content for chunk {i} " * 50,  # Make it long enough to trigger truncation
            similarity_score=0.95 - (i * 0.05),
            rank_position=i,
            accuracy_weight=1.0
        )
    
    tracer.set_llm_info(provider="test", model="test-model")
    chain = tracer.build_reasoning_chain()
    
    assert len(chain.retrieved_chunks) == 5
    
    # Verify chunks are in order
    for i, chunk in enumerate(chain.retrieved_chunks, 1):
        assert chunk.chunk_id == i
        assert chunk.rank_position == i
        assert chunk.repo_name == f"repo-{i}"
        
        # Verify content preview truncation
        if len(f"Content for chunk {i} " * 50) > 200:
            assert chunk.content_preview.endswith("...")
            assert len(chunk.content_preview) <= 203  # 200 chars + "..."


def test_workflow_tracer_no_steps() -> None:
    """Workflow tracer should handle case with no steps."""
    tracer = WorkflowTracer("Simple query")
    
    tracer.set_llm_info(provider="test", model="test")
    chain = tracer.build_reasoning_chain()
    
    assert chain.query == "Simple query"
    assert len(chain.steps) == 0
    assert len(chain.retrieved_chunks) == 0
    assert chain.total_time_ms >= 0


def test_workflow_tracer_timing_breakdown() -> None:
    """Workflow tracer should calculate timing breakdown correctly."""
    tracer = WorkflowTracer("Timing test query")
    
    # Add steps with known timings
    start1 = tracer.start_step("query_embedding")
    time.sleep(0.01)  # 10ms
    tracer.end_step("query_embedding", start1, {})
    
    start2 = tracer.start_step("retrieval")
    time.sleep(0.02)  # 20ms
    tracer.end_step("retrieval", start2, {})
    
    start3 = tracer.start_step("generation")
    time.sleep(0.03)  # 30ms
    tracer.end_step("generation", start3, {})
    
    tracer.set_llm_info(provider="test", model="test")
    chain = tracer.build_reasoning_chain()
    
    # Verify individual timings
    assert chain.query_embedding_time_ms >= 10
    assert chain.retrieval_time_ms >= 20
    assert chain.generation_time_ms >= 30
    
    # Verify total is sum of parts (with some tolerance for timing variations)
    expected_total = chain.query_embedding_time_ms + chain.retrieval_time_ms + chain.generation_time_ms
    assert abs(chain.total_time_ms - expected_total) < 5  # 5ms tolerance


def test_workflow_tracer_chunk_without_section() -> None:
    """Workflow tracer should handle chunks without section titles."""
    tracer = WorkflowTracer("Test query")
    
    tracer.add_retrieved_chunk(
        chunk_id=1,
        repo_name="test-repo",
        file_path="README.md",
        section_title=None,  # No section title
        content="Some content",
        similarity_score=0.9,
        rank_position=1,
        accuracy_weight=1.0
    )
    
    tracer.set_llm_info(provider="test", model="test")
    chain = tracer.build_reasoning_chain()
    
    assert len(chain.retrieved_chunks) == 1
    assert chain.retrieved_chunks[0].section_title is None


def test_workflow_tracer_short_content_no_truncation() -> None:
    """Workflow tracer should not truncate short content."""
    tracer = WorkflowTracer("Test query")
    
    short_content = "This is short content"
    tracer.add_retrieved_chunk(
        chunk_id=1,
        repo_name="test-repo",
        file_path="file.md",
        section_title="Title",
        content=short_content,
        similarity_score=0.9,
        rank_position=1,
        accuracy_weight=1.0
    )
    
    tracer.set_llm_info(provider="test", model="test")
    chain = tracer.build_reasoning_chain()
    
    # Short content should not be truncated
    assert chain.retrieved_chunks[0].content_preview == short_content
    assert not chain.retrieved_chunks[0].content_preview.endswith("...")

