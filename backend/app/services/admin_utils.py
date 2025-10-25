"""
Admin utility service for statistics and analytics.
"""

from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, Integer, case

from app.models import (
    TrainingSession,
    EmbeddingLink,
    KnowledgeChunk,
    WorkflowVector,
    TrainingFeedback
)
from app.schemas.admin import (
    AccuracyStats,
    LLMProviderStats,
    ChunkPerformance
)


def calculate_session_statistics(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> dict:
    """
    Calculate comprehensive session statistics.

    Args:
        db: Database session
        start_date: Filter sessions after this date
        end_date: Filter sessions before this date

    Returns:
        Dictionary with various statistics
    """
    # Build base query
    query = db.query(TrainingSession)

    if start_date:
        query = query.filter(TrainingSession.created_at >= start_date)
    if end_date:
        query = query.filter(TrainingSession.created_at <= end_date)

    total_sessions = query.count()
    sessions_with_feedback = query.filter(TrainingSession.has_feedback == 1).count()
    correct_sessions = query.filter(
        and_(TrainingSession.has_feedback == 1, TrainingSession.is_correct == 1)
    ).count()
    incorrect_sessions = query.filter(
        and_(TrainingSession.has_feedback == 1, TrainingSession.is_correct == 0)
    ).count()

    # Average generation time
    avg_generation_time = db.query(
        func.avg(TrainingSession.generation_time_ms)
    ).filter(
        TrainingSession.generation_time_ms.isnot(None)
    ).scalar()

    return {
        "total_sessions": total_sessions,
        "sessions_with_feedback": sessions_with_feedback,
        "correct_sessions": correct_sessions,
        "incorrect_sessions": incorrect_sessions,
        "pending_feedback": total_sessions - sessions_with_feedback,
        "avg_generation_time_ms": float(avg_generation_time) if avg_generation_time else None,
        "accuracy_rate": (correct_sessions / sessions_with_feedback * 100) if sessions_with_feedback > 0 else None
    }


def get_accuracy_metrics(db: Session) -> AccuracyStats:
    """
    Get accuracy metrics for all sessions.

    Args:
        db: Database session

    Returns:
        Accuracy statistics
    """
    stats = calculate_session_statistics(db)

    return AccuracyStats(
        total_sessions=stats["total_sessions"],
        sessions_with_feedback=stats["sessions_with_feedback"],
        correct_sessions=stats["correct_sessions"],
        incorrect_sessions=stats["incorrect_sessions"],
        pending_feedback=stats["pending_feedback"],
        accuracy_rate=stats["accuracy_rate"]
    )


def get_llm_provider_stats(db: Session) -> List[LLMProviderStats]:
    """
    Get statistics broken down by LLM provider.

    Args:
        db: Database session

    Returns:
        List of provider statistics
    """
    # Get all providers
    providers = db.query(TrainingSession.llm_provider).distinct().all()

    stats = []
    for (provider,) in providers:
        if not provider:
            continue

        # Query for this provider
        provider_sessions = db.query(TrainingSession).filter(
            TrainingSession.llm_provider == provider
        )

        total = provider_sessions.count()
        avg_time = provider_sessions.with_entities(
            func.avg(TrainingSession.generation_time_ms)
        ).scalar()

        correct = provider_sessions.filter(
            and_(
                TrainingSession.has_feedback == 1,
                TrainingSession.is_correct == 1
            )
        ).count()

        incorrect = provider_sessions.filter(
            and_(
                TrainingSession.has_feedback == 1,
                TrainingSession.is_correct == 0
            )
        ).count()

        stats.append(LLMProviderStats(
            provider=provider,
            total_sessions=total,
            avg_generation_time_ms=float(avg_time) if avg_time else None,
            correct_count=correct,
            incorrect_count=incorrect
        ))

    return stats


def get_top_performing_chunks(db: Session, limit: int = 10) -> List[ChunkPerformance]:
    """
    Get top performing chunks based on usefulness and weight.

    Args:
        db: Database session
        limit: Number of chunks to return

    Returns:
        List of top performing chunks
    """
    # Query chunks with their retrieval statistics
    # Use explicit CASE statements to handle NULL values properly
    chunk_stats = db.query(
        KnowledgeChunk.id,
        KnowledgeChunk.repo_name,
        KnowledgeChunk.file_path,
        KnowledgeChunk.section_title,
        KnowledgeChunk.accuracy_weight,
        func.count(EmbeddingLink.id).label('times_retrieved'),
        func.sum(
            case(
                (EmbeddingLink.was_useful == 1, 1),
                else_=0
            )
        ).label('times_useful'),
        func.sum(
            case(
                (EmbeddingLink.was_useful == 0, 1),
                else_=0
            )
        ).label('times_not_useful')
    ).outerjoin(
        EmbeddingLink,
        EmbeddingLink.chunk_id == KnowledgeChunk.id
    ).group_by(
        KnowledgeChunk.id
    ).order_by(
        KnowledgeChunk.accuracy_weight.desc()
    ).limit(limit).all()

    performances = []
    for stat in chunk_stats:
        times_useful = int(stat.times_useful or 0)
        times_not_useful = int(stat.times_not_useful or 0)
        times_retrieved = int(stat.times_retrieved or 0)

        usefulness_rate = None
        if times_useful + times_not_useful > 0:
            usefulness_rate = (times_useful / (times_useful + times_not_useful)) * 100

        performances.append(ChunkPerformance(
            chunk_id=stat.id,
            repo_name=stat.repo_name,
            file_path=stat.file_path,
            section_title=stat.section_title,
            accuracy_weight=float(stat.accuracy_weight),
            times_retrieved=times_retrieved,
            times_useful=times_useful,
            times_not_useful=times_not_useful,
            usefulness_rate=usefulness_rate
        ))

    return performances


def get_underperforming_chunks(db: Session, limit: int = 10) -> List[ChunkPerformance]:
    """
    Get underperforming chunks based on low usefulness or weight.

    Args:
        db: Database session
        limit: Number of chunks to return

    Returns:
        List of underperforming chunks
    """
    # Query chunks with their retrieval statistics
    # Use explicit CASE statements to handle NULL values properly
    chunk_stats = db.query(
        KnowledgeChunk.id,
        KnowledgeChunk.repo_name,
        KnowledgeChunk.file_path,
        KnowledgeChunk.section_title,
        KnowledgeChunk.accuracy_weight,
        func.count(EmbeddingLink.id).label('times_retrieved'),
        func.sum(
            case(
                (EmbeddingLink.was_useful == 1, 1),
                else_=0
            )
        ).label('times_useful'),
        func.sum(
            case(
                (EmbeddingLink.was_useful == 0, 1),
                else_=0
            )
        ).label('times_not_useful')
    ).outerjoin(
        EmbeddingLink,
        EmbeddingLink.chunk_id == KnowledgeChunk.id
    ).group_by(
        KnowledgeChunk.id
    ).having(
        func.count(EmbeddingLink.id) > 0  # Only chunks that have been retrieved
    ).order_by(
        KnowledgeChunk.accuracy_weight.asc()
    ).limit(limit).all()

    performances = []
    for stat in chunk_stats:
        times_useful = int(stat.times_useful or 0)
        times_not_useful = int(stat.times_not_useful or 0)
        times_retrieved = int(stat.times_retrieved or 0)

        usefulness_rate = None
        if times_useful + times_not_useful > 0:
            usefulness_rate = (times_useful / (times_useful + times_not_useful)) * 100

        performances.append(ChunkPerformance(
            chunk_id=stat.id,
            repo_name=stat.repo_name,
            file_path=stat.file_path,
            section_title=stat.section_title,
            accuracy_weight=float(stat.accuracy_weight),
            times_retrieved=times_retrieved,
            times_useful=times_useful,
            times_not_useful=times_not_useful,
            usefulness_rate=usefulness_rate
        ))

    return performances


def validate_chunk_in_session(db: Session, session_id: int, chunk_id: int) -> bool:
    """
    Validate that a chunk was actually retrieved in a given session.

    Args:
        db: Database session
        session_id: Training session ID
        chunk_id: Knowledge chunk ID

    Returns:
        True if chunk was retrieved in session, False otherwise
    """
    link = db.query(EmbeddingLink).filter(
        and_(
            EmbeddingLink.session_id == session_id,
            EmbeddingLink.chunk_id == chunk_id
        )
    ).first()

    return link is not None


def get_workflow_embedding_count(db: Session, successful_only: bool = False) -> int:
    """
    Get count of workflow embeddings.

    Args:
        db: Database session
        successful_only: Only count successful workflows

    Returns:
        Count of workflow embeddings
    """
    query = db.query(WorkflowVector)

    if successful_only:
        query = query.filter(WorkflowVector.is_successful == 1)

    return query.count()


def get_date_range_for_sessions(db: Session) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Get the date range of all training sessions.

    Args:
        db: Database session

    Returns:
        Tuple of (earliest_date, latest_date)
    """
    result = db.query(
        func.min(TrainingSession.created_at),
        func.max(TrainingSession.created_at)
    ).first()

    return result if result else (None, None)
