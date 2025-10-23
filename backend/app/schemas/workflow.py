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

