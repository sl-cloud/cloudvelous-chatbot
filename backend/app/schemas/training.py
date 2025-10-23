"""
Training and feedback DTOs.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ChunkFeedback(BaseModel):
    """Feedback on individual chunk usefulness."""
    
    chunk_id: int
    was_useful: bool


class TrainingFeedbackRequest(BaseModel):
    """Request to provide feedback on a training session."""
    
    session_id: int
    is_correct: bool
    feedback_type: str = Field(..., description="'correct', 'incorrect', or 'needs_improvement'")
    user_correction: Optional[str] = Field(None, description="Corrected answer if incorrect")
    notes: Optional[str] = Field(None, description="Additional notes")
    chunk_feedback: List[ChunkFeedback] = Field(default_factory=list, description="Per-chunk usefulness feedback")


class TrainingFeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    
    success: bool
    message: str
    chunks_updated: int = 0
    workflow_embedding_created: bool = False

