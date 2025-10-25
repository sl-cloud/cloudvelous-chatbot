"""
Embedding inspector router for admin training interface.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import get_db
from app.schemas.inspector import (
    InspectorSessionResponse,
    InspectorComparisonRequest,
    InspectorComparisonResponse,
)
from app.middleware.auth import require_admin_or_api_key
from app.services.inspector_service import InspectorService
from app.exceptions import SessionNotFoundError
from app.utils.rate_limiting import conditional_limiter

router = APIRouter(prefix="/api/embedding-inspector", tags=["inspector"])


@router.get("/{session_id}", response_model=InspectorSessionResponse)
async def inspect_session(
    session_id: int,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_admin_or_api_key)
):
    """
    Get complete embedding inspection details for a training session.

    This endpoint provides everything needed for the admin training interface:
    - Session details (query, response, LLM info)
    - All retrieved chunks with scores and metadata
    - Retrieval statistics
    - Workflow trace visualization
    - Similar workflows that influenced retrieval

    Requires: Admin JWT token or API key

    Args:
        session_id: Training session ID to inspect
        db: Database session
        auth: Authentication info from middleware

    Returns:
        Complete session inspection data

    Raises:
        HTTPException: If session not found or unauthorized
    """
    service = InspectorService(db)
    
    try:
        return await service.inspect_session(session_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/compare", response_model=InspectorComparisonResponse)
@conditional_limiter("15/minute")  # Limit expensive comparison operations
async def compare_sessions(
    request: InspectorComparisonRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_admin_or_api_key)
):
    """
    Compare two training sessions side-by-side.

    Useful for understanding why different queries produced different results
    or for analyzing improvements over time.

    Requires: Admin JWT token or API key

    Args:
        request: Comparison request with two session IDs
        db: Database session
        auth: Authentication info

    Returns:
        Comparison analysis of both sessions
        
    Raises:
        HTTPException: If either session not found
    """
    service = InspectorService(db)
    
    try:
        return await service.compare_sessions(
            request.session_id_1,
            request.session_id_2,
            request.include_chunk_overlap
        )
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
