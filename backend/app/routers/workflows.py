"""
Workflow search router for finding similar reasoning patterns.
"""

import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import get_db, WorkflowVector, TrainingSession, EmbeddingLink
from app.schemas.workflow import (
    WorkflowSearchRequest,
    WorkflowSearchResponse,
    WorkflowSearchResult,
    WorkflowComparisonRequest,
    WorkflowComparisonResponse,
    WorkflowPatternSummary,
)
from app.middleware.auth import require_admin_or_api_key
from app.utils.logging import get_logger
from app.services import get_embedder
from app.config import settings
from app.utils.rate_limiting import conditional_limiter

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


# ========== Helper Functions ==========


async def _get_query_embedding(
    request: WorkflowSearchRequest
) -> List[float]:
    """
    Get or validate query embedding.
    
    Args:
        request: Search request with query text or embedding
        
    Returns:
        Query embedding vector
        
    Raises:
        HTTPException: If embedding is invalid
    """
    if request.query_text:
        embedder = get_embedder()
        return await asyncio.to_thread(
            embedder.embed_text,
            request.query_text
        )
    else:
        query_embedding = request.query_embedding
        if len(query_embedding) != 384:
            raise HTTPException(
                status_code=400,
                detail="Query embedding must be 384-dimensional"
            )
        return query_embedding


def _apply_workflow_filters(
    query,
    request: WorkflowSearchRequest
):
    """
    Apply filters to workflow query.
    
    Args:
        query: SQLAlchemy query object
        request: Search request with filter parameters
        
    Returns:
        Filtered query object
    """
    if request.successful_only:
        query = query.filter(WorkflowVector.is_successful == 1)

    if request.min_confidence > 0:
        query = query.filter(WorkflowVector.confidence >= request.min_confidence)

    if request.start_date:
        query = query.filter(WorkflowVector.created_at >= request.start_date)

    if request.end_date:
        query = query.filter(WorkflowVector.created_at <= request.end_date)
    
    return query


async def _calculate_workflow_similarities(
    workflow_vectors: List[WorkflowVector],
    query_embedding: List[float],
    min_similarity: float,
    log
) -> List[tuple]:
    """
    Calculate similarity scores for workflows in parallel.
    
    Args:
        workflow_vectors: List of workflow vectors to compare
        query_embedding: Query embedding vector
        min_similarity: Minimum similarity threshold
        log: Logger instance
        
    Returns:
        List of (workflow, similarity) tuples above threshold
    """
    embedder = get_embedder()
    similarities = []
    
    # Helper function for similarity calculation
    def calculate_similarity(wf_embedding):
        return float(embedder.cosine_similarity(query_embedding, wf_embedding))

    # Process workflows with embeddings
    tasks = []
    workflow_map = {}
    for wf in workflow_vectors:
        if wf.workflow_embedding:
            workflow_map[wf.id] = wf
            tasks.append((wf.id, asyncio.to_thread(
                calculate_similarity,
                wf.workflow_embedding
            )))
    
    # Wait for all similarity calculations to complete
    for wf_id, task in tasks:
        try:
            similarity = await task
            if similarity >= min_similarity:
                wf = workflow_map[wf_id]
                similarities.append((wf, similarity))
        except Exception as e:
            log.warning(f"Failed to calculate similarity for workflow", error=str(e))
    
    return similarities


def _build_workflow_search_result(
    db: Session,
    wf: WorkflowVector,
    similarity: float,
    log
) -> Optional[WorkflowSearchResult]:
    """
    Build a workflow search result from a workflow vector.
    
    Args:
        db: Database session
        wf: Workflow vector
        similarity: Similarity score
        log: Logger instance
        
    Returns:
        WorkflowSearchResult or None if session not found
    """
    # Get associated session
    session = db.query(TrainingSession).filter(
        TrainingSession.id == wf.session_id
    ).first()

    if not session:
        log.warning(f"Session {wf.session_id} not found for workflow {wf.id}")
        return None

    # Get chunks used in this session
    chunk_links = db.query(EmbeddingLink).filter(
        EmbeddingLink.session_id == wf.session_id
    ).all()

    chunks_used = [link.chunk_id for link in chunk_links]

    # Build response preview
    response_preview = session.response[:200] + "..." if len(session.response) > 200 else session.response

    return WorkflowSearchResult(
        workflow_id=wf.id,
        session_id=wf.session_id,
        similarity_score=round(similarity, 4),
        query=session.query,
        response_preview=response_preview,
        is_successful=wf.is_successful == 1,
        confidence=wf.confidence,
        created_at=wf.created_at,
        llm_provider=session.llm_provider,
        llm_model=session.llm_model,
        chunks_used=chunks_used,
        num_chunks_retrieved=len(chunks_used),
        has_feedback=session.has_feedback == 1,
        is_correct=session.is_correct == 1 if session.is_correct is not None else None
    )


def _build_filters_summary(request: WorkflowSearchRequest) -> dict:
    """
    Build summary of applied filters.
    
    Args:
        request: Search request
        
    Returns:
        Dictionary of applied filters
    """
    return {
        "successful_only": request.successful_only,
        "min_similarity": request.min_similarity,
        "min_confidence": request.min_confidence,
        "start_date": request.start_date.isoformat() if request.start_date else None,
        "end_date": request.end_date.isoformat() if request.end_date else None,
        "top_k": request.top_k
    }


# ========== Endpoint Handlers ==========


@router.post("/search", response_model=WorkflowSearchResponse)
@conditional_limiter("20/minute")  # Limit workflow searches (can be computationally expensive)
async def search_workflows(
    request: WorkflowSearchRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_admin_or_api_key)
):
    """
    Search for similar workflow patterns.

    Use this to find past reasoning chains similar to a new query,
    or to analyze patterns in successful vs unsuccessful workflows.

    Requires: Admin JWT token or API key

    Args:
        request: Search request with query or embedding
        db: Database session
        auth: Authentication info

    Returns:
        List of similar workflows ranked by similarity

    Raises:
        HTTPException: If neither query_text nor query_embedding provided
    """
    log = get_logger(__name__)
    log.info("Searching workflows", has_query_text=bool(request.query_text))

    # Validate input
    if not request.query_text and not request.query_embedding:
        raise HTTPException(
            status_code=400,
            detail="Either query_text or query_embedding must be provided"
        )

    # Get query embedding
    query_embedding = await _get_query_embedding(request)

    # Build and filter workflow query
    query = db.query(WorkflowVector)
    query = _apply_workflow_filters(query, request)
    workflow_vectors = query.all()

    # Calculate similarities in parallel
    similarities = await _calculate_workflow_similarities(
        workflow_vectors,
        query_embedding,
        request.min_similarity,
        log
    )

    # Sort by similarity (descending) and limit
    similarities.sort(key=lambda x: x[1], reverse=True)
    similarities = similarities[:request.top_k]

    # Build results
    results = []
    for wf, similarity in similarities:
        result = _build_workflow_search_result(db, wf, similarity, log)
        if result:
            results.append(result)

    # Build filters summary
    filters_applied = _build_filters_summary(request)

    return WorkflowSearchResponse(
        results=results,
        total_found=len(results),
        query_text=request.query_text,
        search_embedding_dimension=384,
        filters_applied=filters_applied
    )


@router.post("/compare", response_model=WorkflowComparisonResponse)
@conditional_limiter("15/minute")  # Limit expensive workflow comparisons
async def compare_workflows(
    request: WorkflowComparisonRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_admin_or_api_key)
):
    """
    Compare two workflow patterns to understand differences.

    Useful for analyzing why one workflow succeeded and another failed,
    or for understanding how retrieval patterns differ.

    Requires: Admin JWT token or API key

    Args:
        request: Comparison request with two workflow IDs
        db: Database session
        auth: Authentication info

    Returns:
        Detailed comparison of the two workflows
    """
    log = get_logger(__name__)
    log.info(f"Comparing workflows {request.workflow_id_1} and {request.workflow_id_2}")

    # Get both workflows
    wf1 = db.query(WorkflowVector).filter(WorkflowVector.id == request.workflow_id_1).first()
    wf2 = db.query(WorkflowVector).filter(WorkflowVector.id == request.workflow_id_2).first()

    if not wf1:
        raise HTTPException(status_code=404, detail=f"Workflow {request.workflow_id_1} not found")
    if not wf2:
        raise HTTPException(status_code=404, detail=f"Workflow {request.workflow_id_2} not found")

    # Get associated sessions
    session1 = db.query(TrainingSession).filter(TrainingSession.id == wf1.session_id).first()
    session2 = db.query(TrainingSession).filter(TrainingSession.id == wf2.session_id).first()

    if not session1 or not session2:
        raise HTTPException(status_code=404, detail="Associated session not found")

    # Build pattern summaries
    pattern1 = await _build_workflow_pattern(db, wf1, session1)
    pattern2 = await _build_workflow_pattern(db, wf2, session2)

    # Calculate query similarity
    # Run in thread pool to avoid blocking event loop
    query_similarity = None
    if wf1.workflow_embedding and wf2.workflow_embedding:
        embedder = get_embedder()
        query_similarity = await asyncio.to_thread(
            lambda: float(embedder.cosine_similarity(wf1.workflow_embedding, wf2.workflow_embedding))
        )

    # Calculate pattern similarity (composite score)
    pattern_similarity = _calculate_pattern_similarity(pattern1, pattern2)

    # Find common elements
    common_chunks = list(set(pattern1.chunks_retrieved) & set(pattern2.chunks_retrieved))
    common_repos = list(set(pattern1.unique_repos) & set(pattern2.unique_repos))

    # Build analysis
    analysis = {
        "query_length_diff": pattern1.query_length - pattern2.query_length,
        "chunks_diff": pattern1.chunks_retrieved - pattern2.chunks_retrieved,
        "time_diff_ms": (pattern1.total_time_ms or 0) - (pattern2.total_time_ms or 0),
        "similarity_score_diff": pattern1.avg_similarity_score - pattern2.avg_similarity_score,
        "both_successful": pattern1.is_successful and pattern2.is_successful,
        "both_have_feedback": pattern1.has_feedback and pattern2.has_feedback,
        "correctness_matches": pattern1.is_correct == pattern2.is_correct if (pattern1.is_correct is not None and pattern2.is_correct is not None) else None,
    }

    return WorkflowComparisonResponse(
        workflow_1=pattern1,
        workflow_2=pattern2,
        query_similarity=query_similarity,
        pattern_similarity=pattern_similarity,
        common_chunks=common_chunks,
        common_repos=common_repos,
        analysis=analysis
    )


async def _build_workflow_pattern(
    db: Session,
    workflow: WorkflowVector,
    session: TrainingSession
) -> WorkflowPatternSummary:
    """
    Build a workflow pattern summary from a workflow vector and session.

    Args:
        db: Database session
        workflow: Workflow vector
        session: Training session

    Returns:
        Workflow pattern summary
    """
    # Get chunk links
    chunk_links = db.query(EmbeddingLink).filter(
        EmbeddingLink.session_id == session.id
    ).all()

    # Get unique repos and files
    from app.models import KnowledgeChunk
    chunks = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.id.in_([link.chunk_id for link in chunk_links])
    ).all()

    unique_repos = list(set(chunk.repo_name for chunk in chunks))
    unique_files = list(set(chunk.file_path for chunk in chunks))

    # Calculate average similarity score
    avg_similarity = sum(link.similarity_score for link in chunk_links) / len(chunk_links) if chunk_links else 0.0

    # Extract keywords from query (simple word extraction)
    keywords = [word.strip().lower() for word in session.query.split() if len(word.strip()) > 3][:10]

    # Extract timing from reasoning chain
    total_time = None
    retrieval_time = None
    generation_time = None

    if session.reasoning_chain and isinstance(session.reasoning_chain, dict):
        steps = session.reasoning_chain.get("steps", [])
        total_time = sum(step.get("duration_ms", 0) for step in steps)
        retrieval_time = next((step.get("duration_ms") for step in steps if step.get("step_name") == "retrieval"), None)
        generation_time = next((step.get("duration_ms") for step in steps if step.get("step_name") == "generation"), None)

    return WorkflowPatternSummary(
        workflow_id=workflow.id,
        session_id=session.id,
        query_length=len(session.query),
        query_keywords=keywords,
        chunks_retrieved=len(chunk_links),
        unique_repos=unique_repos,
        unique_files=unique_files,
        avg_similarity_score=round(avg_similarity, 4),
        total_time_ms=total_time,
        retrieval_time_ms=retrieval_time,
        generation_time_ms=generation_time,
        is_successful=workflow.is_successful == 1,
        has_feedback=session.has_feedback == 1,
        is_correct=session.is_correct == 1 if session.is_correct is not None else None
    )


def _calculate_pattern_similarity(
    pattern1: WorkflowPatternSummary,
    pattern2: WorkflowPatternSummary
) -> float:
    """
    Calculate a composite similarity score between two patterns.

    Args:
        pattern1: First pattern
        pattern2: Second pattern

    Returns:
        Similarity score between 0 and 1
    """
    scores = []

    # Chunk count similarity
    max_chunks = max(pattern1.chunks_retrieved, pattern2.chunks_retrieved)
    min_chunks = min(pattern1.chunks_retrieved, pattern2.chunks_retrieved)
    chunk_sim = min_chunks / max_chunks if max_chunks > 0 else 1.0
    scores.append(chunk_sim)

    # Repo overlap
    repos1 = set(pattern1.unique_repos)
    repos2 = set(pattern2.unique_repos)
    repo_overlap = len(repos1 & repos2) / len(repos1 | repos2) if (repos1 or repos2) else 1.0
    scores.append(repo_overlap)

    # Similarity score proximity
    sim_diff = abs(pattern1.avg_similarity_score - pattern2.avg_similarity_score)
    sim_proximity = max(0, 1.0 - sim_diff)
    scores.append(sim_proximity)

    # Success alignment
    success_match = 1.0 if pattern1.is_successful == pattern2.is_successful else 0.0
    scores.append(success_match)

    # Weighted average
    weights = [0.3, 0.3, 0.2, 0.2]
    pattern_similarity = sum(score * weight for score, weight in zip(scores, weights))

    return round(pattern_similarity, 4)
