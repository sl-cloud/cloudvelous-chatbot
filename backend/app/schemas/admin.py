"""
Admin-specific schemas for authentication and management.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Authentication Schemas

class AdminLoginRequest(BaseModel):
    """Request schema for admin login."""
    username: str = Field(..., description="Admin username")
    password: str = Field(..., description="Admin password")


class AdminTokenResponse(BaseModel):
    """Response schema for admin login."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


# Session Management Schemas

class AdminSessionFilter(BaseModel):
    """Filter criteria for session listing."""
    start_date: Optional[datetime] = Field(None, description="Filter sessions after this date")
    end_date: Optional[datetime] = Field(None, description="Filter sessions before this date")
    has_feedback: Optional[bool] = Field(None, description="Filter by feedback presence")
    is_correct: Optional[bool] = Field(None, description="Filter by correctness (requires has_feedback=True)")
    llm_provider: Optional[str] = Field(None, description="Filter by LLM provider (openai, gemini)")
    min_generation_time: Optional[int] = Field(None, description="Minimum generation time in ms")
    max_generation_time: Optional[int] = Field(None, description="Maximum generation time in ms")


class AdminSessionListRequest(BaseModel):
    """Request schema for listing training sessions."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Sort field: created_at, generation_time_ms, id")
    sort_order: str = Field(default="desc", description="Sort order: asc, desc")
    filters: Optional[AdminSessionFilter] = Field(None, description="Filter criteria")


class AdminSessionSummary(BaseModel):
    """Summary of a training session for listing."""
    session_id: int
    query: str
    response_preview: str = Field(..., description="First 200 characters of response")
    llm_provider: str
    llm_model: str
    generation_time_ms: Optional[float]
    has_feedback: int
    is_correct: Optional[int]
    chunks_retrieved: int
    created_at: datetime

    class Config:
        from_attributes = True


class AdminSessionListResponse(BaseModel):
    """Response schema for session listing."""
    sessions: List[AdminSessionSummary]
    total_count: int = Field(..., description="Total number of sessions matching filters")
    page: int
    page_size: int
    total_pages: int


# Bulk Operations Schemas

class ChunkFeedbackItem(BaseModel):
    """Feedback for a single chunk."""
    chunk_id: int
    was_useful: bool


class BulkFeedbackItem(BaseModel):
    """Feedback for a single session."""
    session_id: int
    is_correct: bool
    feedback_type: str = Field(default="admin_review", description="Type of feedback")
    chunk_feedback: Optional[List[ChunkFeedbackItem]] = None
    user_correction: Optional[str] = None
    notes: Optional[str] = None


class BulkFeedbackRequest(BaseModel):
    """Request schema for bulk feedback submission."""
    feedback_items: List[BulkFeedbackItem] = Field(..., description="List of feedback items")


class BulkFeedbackResult(BaseModel):
    """Result for a single feedback item."""
    session_id: int
    success: bool
    error: Optional[str] = None
    chunks_updated: int = 0
    workflow_embedding_created: bool = False


class BulkFeedbackResponse(BaseModel):
    """Response schema for bulk feedback submission."""
    results: List[BulkFeedbackResult]
    total_processed: int
    successful: int
    failed: int


# Chunk Management Schemas

class ChunkWeightAdjustment(BaseModel):
    """Request schema for manual chunk weight adjustment."""
    chunk_id: int
    new_weight: float = Field(..., ge=0.5, le=2.0, description="New accuracy weight (0.5 to 2.0)")
    reason: Optional[str] = Field(None, description="Reason for manual adjustment")


class ChunkWeightAdjustmentResponse(BaseModel):
    """Response schema for chunk weight adjustment."""
    success: bool
    chunk_id: int
    old_weight: float
    new_weight: float
    message: str


# Statistics Schemas

class AccuracyStats(BaseModel):
    """Accuracy statistics for sessions."""
    total_sessions: int
    sessions_with_feedback: int
    correct_sessions: int
    incorrect_sessions: int
    pending_feedback: int
    accuracy_rate: Optional[float] = Field(None, description="Percentage of correct sessions")


class LLMProviderStats(BaseModel):
    """Statistics by LLM provider."""
    provider: str
    total_sessions: int
    avg_generation_time_ms: Optional[float]
    correct_count: int
    incorrect_count: int


class ChunkPerformance(BaseModel):
    """Performance metrics for a knowledge chunk."""
    chunk_id: int
    repo_name: str
    file_path: str
    section_title: Optional[str]
    accuracy_weight: float
    times_retrieved: int
    times_useful: int
    times_not_useful: int
    usefulness_rate: Optional[float] = Field(None, description="Percentage of times marked useful")


class AdminStatsResponse(BaseModel):
    """Response schema for admin statistics."""
    accuracy_stats: AccuracyStats
    provider_stats: List[LLMProviderStats]
    top_performing_chunks: List[ChunkPerformance]
    underperforming_chunks: List[ChunkPerformance]
    total_workflow_embeddings: int
    date_range: dict = Field(..., description="Date range for statistics")


# Export Schemas

class SessionExportRequest(BaseModel):
    """Request schema for session data export."""
    format: str = Field(default="json", description="Export format: json, csv")
    filters: Optional[AdminSessionFilter] = None
    include_full_response: bool = Field(default=False, description="Include full response text")
    include_reasoning_chain: bool = Field(default=False, description="Include reasoning chain")
