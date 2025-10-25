"""
Admin service layer for session management and bulk operations.

This service encapsulates business logic for admin operations,
separating it from the HTTP layer for better testability and reuse.
"""

import math
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.models import TrainingSession, KnowledgeChunk, TrainingFeedback, EmbeddingLink
from app.schemas.admin import (
    AdminSessionListRequest,
    AdminSessionListResponse,
    AdminSessionSummary,
    BulkFeedbackRequest,
    BulkFeedbackResponse,
    BulkFeedbackResult,
    ChunkWeightAdjustment,
    ChunkWeightAdjustmentResponse,
    AdminStatsResponse,
)
from app.services.admin_utils import (
    get_accuracy_metrics,
    get_llm_provider_stats,
    get_top_performing_chunks,
    get_underperforming_chunks,
    get_workflow_embedding_count,
    get_date_range_for_sessions
)
from app.services import get_workflow_learner
from app.config import settings
from app.utils.logging import get_logger
from app.exceptions import (
    ValidationError,
    ChunkNotFoundError,
    SessionNotFoundError,
    DatabaseOperationError,
    BulkOperationError
)


class AdminService:
    """Service layer for admin operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.log = get_logger(__name__)
    
    def list_sessions(
        self,
        request: AdminSessionListRequest
    ) -> AdminSessionListResponse:
        """
        List training sessions with filtering, sorting, and pagination.
        
        Args:
            request: Session list request with filters and pagination
            
        Returns:
            Paginated list of training sessions
            
        Raises:
            ValueError: If pagination parameters are invalid
        """
        self.log.info(f"Listing sessions - page {request.page}", page=request.page)
        
        # Build base query
        query = self.db.query(TrainingSession)
        
        # Apply filters
        query = self._apply_session_filters(query, request)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        query = self._apply_sorting(query, request.sort_by, request.sort_order)
        
        # Apply pagination
        offset = (request.page - 1) * request.page_size
        query = query.offset(offset).limit(request.page_size)
        
        # Execute query
        sessions = query.all()
        
        # Batch fetch chunk counts to avoid N+1
        summaries = self._build_session_summaries(sessions)
        
        # Calculate total pages
        total_pages = math.ceil(total_count / request.page_size) if total_count > 0 else 0
        
        return AdminSessionListResponse(
            sessions=summaries,
            total_count=total_count,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages
        )
    
    def _apply_session_filters(self, query, request: AdminSessionListRequest):
        """Apply filters to session query."""
        if not request.filters:
            return query
            
        filters = request.filters
        
        if filters.start_date:
            query = query.filter(TrainingSession.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(TrainingSession.created_at <= filters.end_date)
        
        if filters.has_feedback is not None:
            query = query.filter(
                TrainingSession.has_feedback == (1 if filters.has_feedback else 0)
            )
        
        if filters.is_correct is not None:
            query = query.filter(
                TrainingSession.has_feedback == 1,
                TrainingSession.is_correct == (1 if filters.is_correct else 0)
            )
        
        if filters.llm_provider:
            query = query.filter(TrainingSession.llm_provider == filters.llm_provider)
        
        if filters.min_generation_time:
            query = query.filter(
                TrainingSession.generation_time_ms >= filters.min_generation_time
            )
        
        if filters.max_generation_time:
            query = query.filter(
                TrainingSession.generation_time_ms <= filters.max_generation_time
            )
        
        return query
    
    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to query."""
        sort_column = {
            "created_at": TrainingSession.created_at,
            "generation_time_ms": TrainingSession.generation_time_ms,
            "id": TrainingSession.id,
        }.get(sort_by, TrainingSession.created_at)
        
        if sort_order == "desc":
            return query.order_by(sort_column.desc())
        return query.order_by(sort_column.asc())
    
    def _build_session_summaries(
        self,
        sessions: List[TrainingSession]
    ) -> List[AdminSessionSummary]:
        """Build session summaries with batch-fetched chunk counts."""
        if not sessions:
            return []
        
        # Batch fetch chunk counts to avoid N+1
        session_ids = [s.id for s in sessions]
        chunk_counts = dict(
            self.db.query(
                EmbeddingLink.session_id,
                func.count(EmbeddingLink.id)
            ).filter(
                EmbeddingLink.session_id.in_(session_ids)
            ).group_by(
                EmbeddingLink.session_id
            ).all()
        )
        
        summaries = []
        for session in sessions:
            chunk_count = chunk_counts.get(session.id, 0)
            response_preview = (
                session.response[:200] + "..." 
                if len(session.response) > 200 
                else session.response
            )
            
            summaries.append(AdminSessionSummary(
                session_id=session.id,
                query=session.query,
                response_preview=response_preview,
                llm_provider=session.llm_provider,
                llm_model=session.llm_model,
                generation_time_ms=session.generation_time_ms,
                has_feedback=session.has_feedback,
                is_correct=session.is_correct,
                chunks_retrieved=chunk_count,
                created_at=session.created_at
            ))
        
        return summaries
    
    def submit_bulk_feedback(
        self,
        request: BulkFeedbackRequest
    ) -> BulkFeedbackResponse:
        """
        Submit feedback for multiple sessions in bulk.
        
        Args:
            request: Bulk feedback request
            
        Returns:
            Results for each feedback item
            
        Raises:
            ValidationError: If bulk size exceeds maximum
            DatabaseOperationError: If commit fails
        """
        self.log.info(f"Bulk feedback submission - {len(request.feedback_items)} items")
        
        if len(request.feedback_items) > settings.MAX_BULK_FEEDBACK_SIZE:
            raise ValidationError(
                f"Bulk size exceeds maximum of {settings.MAX_BULK_FEEDBACK_SIZE}"
            )
        
        results = []
        successful = 0
        failed = 0
        
        workflow_learner = get_workflow_learner()
        
        for item in request.feedback_items:
            result = self._process_single_feedback(item, workflow_learner)
            results.append(result)
            
            if result.success:
                successful += 1
            else:
                failed += 1
        
        # Commit the main transaction
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            self.log.error(
                "Failed to commit bulk feedback transaction",
                error=str(e),
                exc_info=True
            )
            raise DatabaseOperationError(
                "Failed to save bulk feedback",
                details={"error_type": type(e).__name__}
            )
        
        return BulkFeedbackResponse(
            results=results,
            total_processed=len(request.feedback_items),
            successful=successful,
            failed=failed
        )
    
    def _process_single_feedback(self, item, workflow_learner) -> BulkFeedbackResult:
        """Process feedback for a single session with savepoint isolation."""
        savepoint = self.db.begin_nested()
        
        try:
            session = self.db.query(TrainingSession).filter(
                TrainingSession.id == item.session_id
            ).first()
            
            if not session:
                savepoint.rollback()
                return BulkFeedbackResult(
                    session_id=item.session_id,
                    success=False,
                    error="Session not found"
                )
            
            # Create feedback record
            feedback = TrainingFeedback(
                session_id=item.session_id,
                feedback_type=item.feedback_type,
                is_correct=item.is_correct,
                user_correction=item.user_correction,
                notes=item.notes
            )
            self.db.add(feedback)
            
            # Update session
            session.has_feedback = 1
            session.is_correct = 1 if item.is_correct else 0
            
            # Process chunk feedback
            chunks_updated = self._update_chunk_feedback(item)
            
            # Create workflow embedding if correct
            workflow_embedding_created = False
            if item.is_correct and settings.WORKFLOW_EMBEDDING_ENABLED:
                workflow_vector = workflow_learner.create_workflow_embedding(
                    db=self.db,
                    session_id=item.session_id,
                    is_successful=True,
                    confidence=1.0
                )
                if workflow_vector:
                    workflow_embedding_created = True
            
            savepoint.commit()
            
            return BulkFeedbackResult(
                session_id=item.session_id,
                success=True,
                chunks_updated=chunks_updated,
                workflow_embedding_created=workflow_embedding_created
            )
            
        except SQLAlchemyError as e:
            savepoint.rollback()
            self.log.error(
                "Database error processing feedback",
                session_id=item.session_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return BulkFeedbackResult(
                session_id=item.session_id,
                success=False,
                error="Database operation failed"
            )
        except Exception as e:
            savepoint.rollback()
            self.log.error(
                "Unexpected error processing feedback",
                session_id=item.session_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return BulkFeedbackResult(
                session_id=item.session_id,
                success=False,
                error="Internal processing error"
            )
    
    def _update_chunk_feedback(self, item) -> int:
        """Update chunk feedback and accuracy weights."""
        chunks_updated = 0
        
        if not item.chunk_feedback:
            return chunks_updated
        
        for chunk_fb in item.chunk_feedback:
            link = self.db.query(EmbeddingLink).filter(
                EmbeddingLink.session_id == item.session_id,
                EmbeddingLink.chunk_id == chunk_fb.chunk_id
            ).first()
            
            if not link:
                continue
            
            link.was_useful = chunk_fb.was_useful
            
            chunk = self.db.query(KnowledgeChunk).filter(
                KnowledgeChunk.id == chunk_fb.chunk_id
            ).first()
            
            if not chunk:
                continue
            
            if chunk_fb.was_useful and item.is_correct:
                chunk.accuracy_weight = min(
                    chunk.accuracy_weight + settings.CHUNK_WEIGHT_ADJUSTMENT_RATE,
                    settings.MAX_CHUNK_WEIGHT
                )
                chunks_updated += 1
            elif not chunk_fb.was_useful:
                chunk.accuracy_weight = max(
                    chunk.accuracy_weight - settings.CHUNK_WEIGHT_ADJUSTMENT_RATE,
                    settings.MIN_CHUNK_WEIGHT
                )
                chunks_updated += 1
        
        return chunks_updated
    
    def adjust_chunk_weight(
        self,
        request: ChunkWeightAdjustment
    ) -> ChunkWeightAdjustmentResponse:
        """
        Manually adjust the accuracy weight of a knowledge chunk.
        
        Args:
            request: Chunk weight adjustment request
            
        Returns:
            Adjustment confirmation
            
        Raises:
            ChunkNotFoundError: If chunk not found
            DatabaseOperationError: If commit fails
        """
        self.log.info(
            "Manual chunk weight adjustment",
            chunk_id=request.chunk_id,
            new_weight=request.new_weight
        )
        
        chunk = self.db.query(KnowledgeChunk).filter(
            KnowledgeChunk.id == request.chunk_id
        ).first()
        
        if not chunk:
            raise ChunkNotFoundError(
                f"Knowledge chunk {request.chunk_id} not found",
                details={"chunk_id": request.chunk_id}
            )
        
        old_weight = chunk.accuracy_weight
        chunk.accuracy_weight = request.new_weight
        
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            self.log.error(
                "Failed to update chunk weight",
                chunk_id=request.chunk_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise DatabaseOperationError(
                "Failed to update chunk weight",
                details={"chunk_id": request.chunk_id}
            )
        
        self.log.info(
            "Chunk weight adjusted",
            chunk_id=request.chunk_id,
            old_weight=old_weight,
            new_weight=request.new_weight,
            reason=request.reason
        )
        
        return ChunkWeightAdjustmentResponse(
            success=True,
            chunk_id=request.chunk_id,
            old_weight=old_weight,
            new_weight=request.new_weight,
            message=f"Chunk weight adjusted from {old_weight:.2f} to {request.new_weight:.2f}"
        )
    
    def get_admin_stats(self) -> AdminStatsResponse:
        """
        Get comprehensive statistics for the admin dashboard.
        
        Returns:
            Comprehensive statistics
        """
        self.log.info("Fetching admin statistics")
        
        accuracy_stats = get_accuracy_metrics(self.db)
        provider_stats = get_llm_provider_stats(self.db)
        top_chunks = get_top_performing_chunks(self.db, limit=10)
        underperforming_chunks = get_underperforming_chunks(self.db, limit=10)
        total_workflow_embeddings = get_workflow_embedding_count(self.db)
        earliest_date, latest_date = get_date_range_for_sessions(self.db)
        
        date_range = {
            "earliest_session": earliest_date.isoformat() if earliest_date else None,
            "latest_session": latest_date.isoformat() if latest_date else None
        }
        
        return AdminStatsResponse(
            accuracy_stats=accuracy_stats,
            provider_stats=provider_stats,
            top_performing_chunks=top_chunks,
            underperforming_chunks=underperforming_chunks,
            total_workflow_embeddings=total_workflow_embeddings,
            date_range=date_range
        )

