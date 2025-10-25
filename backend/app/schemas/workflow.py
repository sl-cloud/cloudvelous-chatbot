"""
Workflow trace and reasoning chain DTOs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class RetrievedChunkTrace(BaseModel):
    """Information about a retrieved chunk in the reasoning chain."""
    
    chunk_id: int
    repo_name: str
    file_path: str
    section_title: Optional[str] = None
    content_preview: str  # First 200 chars
    similarity_score: float
    rank_position: int
    accuracy_weight: float


class WorkflowStep(BaseModel):
    """Individual step in the workflow reasoning chain."""
    
    step_name: str  # e.g., "query_embedding", "retrieval", "generation"
    timestamp: datetime
    duration_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningChain(BaseModel):
    """Complete reasoning chain for a RAG workflow."""
    
    query: str
    query_embedding_time_ms: float
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    
    steps: List[WorkflowStep]
    retrieved_chunks: List[RetrievedChunkTrace]
    workflow_context: Optional[Dict[str, Any]] = None
    
    llm_provider: str
    llm_model: Optional[str] = None


class WorkflowTrace(BaseModel):
    """Complete workflow trace with response."""
    
    session_id: int
    query: str
    response: str
    reasoning_chain: ReasoningChain
    created_at: datetime


class WorkflowSummary(BaseModel):
    """Summary of workflow reasoning for embedding generation."""

    session_id: int
    query: str
    reasoning_text: str  # Natural language summary
    successful: bool
    confidence: float = 1.0


# Phase 3: Workflow Search Schemas

class WorkflowSearchRequest(BaseModel):
    """Request schema for searching similar workflows."""

    query_text: Optional[str] = Field(None, description="Search by query text (will be embedded)")
    query_embedding: Optional[List[float]] = Field(None, description="Search by pre-computed embedding (384-dim)")

    # Filters
    successful_only: bool = Field(default=False, description="Only return successful workflows")
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum confidence score")

    # Date range filters
    start_date: Optional[datetime] = Field(None, description="Filter workflows after this date")
    end_date: Optional[datetime] = Field(None, description="Filter workflows before this date")

    # Pagination
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class WorkflowSearchResult(BaseModel):
    """Individual workflow search result."""

    workflow_id: int
    session_id: int
    similarity_score: float

    # Session info
    query: str
    response_preview: str = Field(..., description="First 200 characters of response")

    # Metadata
    is_successful: bool
    confidence: float
    created_at: datetime

    # LLM info
    llm_provider: str
    llm_model: Optional[str]

    # Retrieved chunks summary
    chunks_used: List[int] = Field(..., description="Chunk IDs that were retrieved")
    num_chunks_retrieved: int

    # Feedback info
    has_feedback: bool
    is_correct: Optional[bool]


class WorkflowSearchResponse(BaseModel):
    """Response schema for workflow search."""

    results: List[WorkflowSearchResult]
    total_found: int
    query_text: Optional[str] = Field(None, description="Original query text if provided")
    search_embedding_dimension: int = Field(default=384)
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Summary of filters applied")


class WorkflowComparisonRequest(BaseModel):
    """Request to compare workflow patterns between two workflows."""

    workflow_id_1: int
    workflow_id_2: int


class WorkflowPatternSummary(BaseModel):
    """Summary of workflow patterns for analysis."""

    workflow_id: int
    session_id: int

    # Query characteristics
    query_length: int
    query_keywords: List[str] = Field(..., description="Key terms extracted from query")

    # Retrieval patterns
    chunks_retrieved: int
    unique_repos: List[str]
    unique_files: List[str]
    avg_similarity_score: float

    # Timing patterns
    total_time_ms: Optional[float]
    retrieval_time_ms: Optional[float]
    generation_time_ms: Optional[float]

    # Success metrics
    is_successful: bool
    has_feedback: bool
    is_correct: Optional[bool]


class WorkflowComparisonResponse(BaseModel):
    """Response comparing two workflow patterns."""

    workflow_1: WorkflowPatternSummary
    workflow_2: WorkflowPatternSummary

    # Similarity metrics
    query_similarity: Optional[float] = Field(None, description="Cosine similarity between queries")
    pattern_similarity: float = Field(..., description="Overall pattern similarity score")

    # Differences
    common_chunks: List[int] = Field(..., description="Chunks retrieved in both workflows")
    common_repos: List[str] = Field(..., description="Repos used in both workflows")

    # Analysis
    analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed analysis of pattern differences"
    )
