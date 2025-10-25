"""
Schemas for the embedding inspector endpoint.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class InspectorChunkDetail(BaseModel):
    """Detailed information about a retrieved chunk."""
    chunk_id: int
    repo_name: str
    file_path: str
    section_title: Optional[str]
    content: str
    content_preview: str = Field(..., description="First 300 characters of content")
    embedding_dimension: int = Field(default=384, description="Dimension of the embedding vector")

    # Retrieval metadata
    similarity_score: float = Field(..., description="Cosine similarity score at retrieval time")
    rank_position: int = Field(..., description="Position in retrieval results (1-indexed)")
    was_useful: Optional[int] = Field(None, description="User feedback: 1=useful, 0=not useful, null=no feedback")

    # Learning metadata
    accuracy_weight: float = Field(..., description="Current accuracy weight (0.5 to 2.0)")
    weight_history: Optional[str] = Field(None, description="Description of weight changes over time")

    class Config:
        from_attributes = True


class RetrievalStatistics(BaseModel):
    """Statistics about chunk retrieval for this session."""
    total_chunks_retrieved: int
    avg_similarity_score: float
    min_similarity_score: float
    max_similarity_score: float
    chunks_marked_useful: int
    chunks_marked_not_useful: int
    chunks_without_feedback: int


class WorkflowTraceStep(BaseModel):
    """Individual step in the workflow trace."""
    step_name: str
    duration_ms: Optional[float]
    metadata: Optional[Dict[str, Any]]


class WorkflowTraceVisualization(BaseModel):
    """Visualization-ready workflow trace."""
    total_duration_ms: Optional[float]
    steps: List[WorkflowTraceStep]
    query_embedding_time_ms: Optional[float]
    retrieval_time_ms: Optional[float]
    generation_time_ms: Optional[float]
    workflow_search_time_ms: Optional[float]


class SimilarWorkflowPreview(BaseModel):
    """Preview of similar workflows that influenced this session."""
    workflow_id: int
    session_id: int
    similarity_score: float
    query_preview: str = Field(..., description="First 100 characters of the similar query")
    was_successful: bool
    chunks_influenced: List[int] = Field(..., description="Chunk IDs that were boosted from this workflow")


class InspectorSessionResponse(BaseModel):
    """Complete session details for the embedding inspector."""

    # Session basics
    session_id: int
    query: str
    response: str
    created_at: datetime

    # LLM details
    llm_provider: str
    llm_model: str
    generation_time_ms: Optional[int]

    # Feedback status
    has_feedback: int
    is_correct: Optional[int]
    feedback_type: Optional[str]
    feedback_notes: Optional[str]

    # Retrieved chunks with full details
    retrieved_chunks: List[InspectorChunkDetail]

    # Statistics
    retrieval_statistics: RetrievalStatistics

    # Workflow trace
    reasoning_chain: Optional[Dict[str, Any]] = Field(None, description="Complete reasoning chain JSON")
    workflow_trace: Optional[WorkflowTraceVisualization] = Field(None, description="Parsed and formatted workflow trace")

    # Similar workflows that influenced retrieval
    similar_workflows: Optional[List[SimilarWorkflowPreview]] = Field(None, description="Similar workflows that boosted chunks")

    # Metadata for UI visualization
    visualization_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for UI visualization"
    )


class InspectorComparisonRequest(BaseModel):
    """Request to compare two sessions."""
    session_id_1: int
    session_id_2: int
    include_chunk_overlap: bool = Field(default=True, description="Include analysis of overlapping chunks")


class ChunkOverlapAnalysis(BaseModel):
    """Analysis of chunk overlap between two sessions."""
    common_chunks: List[int] = Field(..., description="Chunk IDs present in both sessions")
    only_in_session_1: List[int]
    only_in_session_2: List[int]
    overlap_percentage: float = Field(..., description="Percentage of chunks that overlap")


class InspectorComparisonResponse(BaseModel):
    """Response comparing two sessions."""
    session_1: InspectorSessionResponse
    session_2: InspectorSessionResponse

    # Comparison analysis
    query_similarity: Optional[float] = Field(None, description="Similarity between the two queries")
    response_similarity: Optional[float] = Field(None, description="Similarity between the two responses")
    chunk_overlap: Optional[ChunkOverlapAnalysis] = None

    # Difference highlights
    differences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key differences between the sessions"
    )
