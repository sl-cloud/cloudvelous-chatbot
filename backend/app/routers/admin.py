"""
Admin management router for session management and bulk operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import get_db
from app.schemas.admin import (
    AdminSessionListRequest,
    AdminSessionListResponse,
    BulkFeedbackRequest,
    BulkFeedbackResponse,
    ChunkWeightAdjustment,
    ChunkWeightAdjustmentResponse,
    AdminStatsResponse,
)
from app.middleware.auth import require_admin_or_api_key
from app.services.admin_service import AdminService
from app.exceptions import (
    ValidationError,
    ChunkNotFoundError,
    DatabaseOperationError
)
from app.utils.rate_limiting import conditional_limiter

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/sessions", response_model=AdminSessionListResponse)
@conditional_limiter("30/minute")  # Reasonable limit for session listing
async def list_sessions(
    request: AdminSessionListRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin_or_api_key)
):
    """
    List training sessions with filtering, sorting, and pagination.

    Requires: Admin JWT token or API key

    Args:
        request: Session list request with filters and pagination
        db: Database session
        admin: Admin authentication info

    Returns:
        Paginated list of training sessions
    """
    service = AdminService(db)
    return service.list_sessions(request)


@router.post("/bulk-feedback", response_model=BulkFeedbackResponse)
@conditional_limiter("10/minute")  # Strict limit for bulk operations to prevent abuse
async def submit_bulk_feedback(
    request: BulkFeedbackRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin_or_api_key)
):
    """
    Submit feedback for multiple sessions in bulk.

    This is more efficient than calling /api/train multiple times.
    Maximum bulk size is configurable (default 100).

    Requires: Admin JWT token or API key

    Args:
        request: Bulk feedback request
        db: Database session
        admin: Admin authentication info

    Returns:
        Results for each feedback item
        
    Raises:
        HTTPException: If bulk size exceeds maximum or commit fails
    """
    service = AdminService(db)
    
    try:
        return service.submit_bulk_feedback(request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except DatabaseOperationError as e:
        raise HTTPException(status_code=500, detail=e.message)


@router.post("/chunk-edit", response_model=ChunkWeightAdjustmentResponse)
async def adjust_chunk_weight(
    request: ChunkWeightAdjustment,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin_or_api_key)
):
    """
    Manually adjust the accuracy weight of a knowledge chunk.

    Use this for manual intervention when a chunk consistently performs
    well or poorly but hasn't received enough feedback yet.

    Requires: Admin JWT token or API key

    Args:
        request: Chunk weight adjustment request
        db: Database session
        admin: Admin authentication info

    Returns:
        Adjustment confirmation
        
    Raises:
        HTTPException: If chunk not found or database operation fails
    """
    service = AdminService(db)
    
    try:
        return service.adjust_chunk_weight(request)
    except ChunkNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseOperationError as e:
        raise HTTPException(status_code=500, detail=e.message)


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin_or_api_key)
):
    """
    Get comprehensive statistics for the admin dashboard.

    Includes:
    - Accuracy metrics (correct/incorrect/pending sessions)
    - LLM provider performance comparison
    - Top and underperforming chunks
    - Workflow embedding count

    Requires: Admin JWT token or API key

    Args:
        db: Database session
        admin: Admin authentication info

    Returns:
        Comprehensive statistics
    """
    service = AdminService(db)
    return service.get_admin_stats()
