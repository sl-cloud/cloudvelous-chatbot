"""
Training router for feedback endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import get_db, TrainingSession, TrainingFeedback, EmbeddingLink, KnowledgeChunk
from app.schemas.training import TrainingFeedbackRequest, TrainingFeedbackResponse
from app.services import get_workflow_learner
from app.config import settings


router = APIRouter(prefix="/api", tags=["training"])


@router.post("/train", response_model=TrainingFeedbackResponse)
async def submit_feedback(
    request: TrainingFeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit feedback on a training session.
    
    This endpoint:
    1. Records feedback on the training session
    2. Updates chunk accuracy weights based on usefulness
    3. Creates workflow embeddings for successful sessions
    
    Args:
        request: Feedback request
        db: Database session
        
    Returns:
        Feedback response with update summary
    """
    try:
        # Get training session
        session = db.query(TrainingSession).filter(
            TrainingSession.id == request.session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Training session not found")
        
        # Create feedback record
        feedback = TrainingFeedback(
            session_id=request.session_id,
            feedback_type=request.feedback_type,
            is_correct=request.is_correct,
            user_correction=request.user_correction,
            notes=request.notes
        )
        db.add(feedback)
        
        # Update training session
        session.has_feedback = 1
        session.is_correct = 1 if request.is_correct else 0
        
        # Process chunk feedback
        chunks_updated = 0
        if request.chunk_feedback:
            for chunk_fb in request.chunk_feedback:
                # Find the embedding link
                link = db.query(EmbeddingLink).filter(
                    EmbeddingLink.session_id == request.session_id,
                    EmbeddingLink.chunk_id == chunk_fb.chunk_id
                ).first()
                
                if link:
                    # Update usefulness flag
                    link.was_useful = chunk_fb.was_useful
                    
                    # Update chunk accuracy weight
                    chunk = db.query(KnowledgeChunk).filter(
                        KnowledgeChunk.id == chunk_fb.chunk_id
                    ).first()
                    
                    if chunk:
                        if chunk_fb.was_useful and request.is_correct:
                            # Increase weight for useful chunks in correct answers
                            chunk.accuracy_weight = min(
                                chunk.accuracy_weight + settings.CHUNK_WEIGHT_ADJUSTMENT_RATE,
                                settings.MAX_CHUNK_WEIGHT
                            )
                            chunks_updated += 1
                        elif not chunk_fb.was_useful:
                            # Decrease weight for not useful chunks
                            chunk.accuracy_weight = max(
                                chunk.accuracy_weight - settings.CHUNK_WEIGHT_ADJUSTMENT_RATE,
                                settings.MIN_CHUNK_WEIGHT
                            )
                            chunks_updated += 1
        
        # Create workflow embedding if answer was correct
        workflow_embedding_created = False
        if request.is_correct and settings.WORKFLOW_EMBEDDING_ENABLED:
            workflow_learner = get_workflow_learner()
            workflow_vector = workflow_learner.create_workflow_embedding(
                db=db,
                session_id=request.session_id,
                is_successful=True,
                confidence=1.0
            )
            if workflow_vector:
                workflow_embedding_created = True
        
        db.commit()
        
        return TrainingFeedbackResponse(
            success=True,
            message="Feedback recorded successfully",
            chunks_updated=chunks_updated,
            workflow_embedding_created=workflow_embedding_created
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing feedback: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_training_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details of a training session.
    
    Args:
        session_id: Training session ID
        db: Database session
        
    Returns:
        Training session details with retrieved chunks
    """
    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Training session not found")
    
    # Get embedding links with chunk details
    links = db.query(EmbeddingLink, KnowledgeChunk).join(
        KnowledgeChunk,
        EmbeddingLink.chunk_id == KnowledgeChunk.id
    ).filter(
        EmbeddingLink.session_id == session_id
    ).all()
    
    chunks_info = []
    for link, chunk in links:
        chunks_info.append({
            "chunk_id": chunk.id,
            "repo_name": chunk.repo_name,
            "file_path": chunk.file_path,
            "section_title": chunk.section_title,
            "content": chunk.content,
            "similarity_score": link.similarity_score,
            "rank_position": link.rank_position,
            "was_useful": link.was_useful,
            "accuracy_weight": chunk.accuracy_weight
        })
    
    return {
        "session_id": session.id,
        "query": session.query,
        "response": session.response,
        "reasoning_chain": session.reasoning_chain,
        "retrieved_chunks": chunks_info,
        "llm_provider": session.llm_provider,
        "llm_model": session.llm_model,
        "generation_time_ms": session.generation_time_ms,
        "has_feedback": session.has_feedback,
        "is_correct": session.is_correct,
        "created_at": session.created_at
    }

