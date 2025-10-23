"""
Training feedback table for user corrections.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func

from app.models.database import Base


class TrainingFeedback(Base):
    """User feedback on chatbot responses for training."""
    
    __tablename__ = "training_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False, index=True)
    feedback_type = Column(String(50), nullable=False)  # 'correct', 'incorrect', 'needs_improvement'
    is_correct = Column(Boolean, nullable=True)
    user_correction = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<TrainingFeedback(id={self.id}, session_id={self.session_id}, type={self.feedback_type})>"

