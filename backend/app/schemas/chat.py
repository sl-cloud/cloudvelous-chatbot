"""
Chat endpoint request/response DTOs.
"""

from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.workflow import ReasoningChain


class ChatRequest(BaseModel):
    """Request for /api/ask endpoint."""
    
    question: str = Field(..., min_length=1, max_length=5000)
    include_trace: bool = Field(default=False, description="Include full reasoning trace in response")


class ChatResponse(BaseModel):
    """Response from /api/ask endpoint."""
    
    answer: str
    session_id: int
    sources: List[str] = Field(default_factory=list, description="Source files/repos used")
    
    # Optional workflow trace (only if requested)
    reasoning_chain: Optional[ReasoningChain] = None


class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str
    detail: Optional[str] = None

