"""
Training sessions table for workflow reasoning capture.
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, func

from app.models.database import Base


class TrainingSession(Base):
    """Training session capturing complete RAG workflow reasoning chain."""
    
    __tablename__ = "training_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    
    # Reasoning chain capture
    reasoning_chain = Column(JSON, nullable=False)  # Full workflow trace
    retrieved_chunks = Column(JSON, nullable=False)  # Chunks with scores
    workflow_context = Column(JSON, nullable=True)  # Repo relationships
    
    # Generation metadata
    llm_provider = Column(String(50), nullable=False)
    llm_model = Column(String(100), nullable=True)
    generation_time_ms = Column(Float, nullable=True)
    
    # Feedback status
    has_feedback = Column(Integer, default=0)  # 0=pending, 1=has feedback
    is_correct = Column(Integer, nullable=True)  # NULL=pending, 1=correct, 0=incorrect
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<TrainingSession(id={self.id}, query='{self.query[:50]}...')>"

