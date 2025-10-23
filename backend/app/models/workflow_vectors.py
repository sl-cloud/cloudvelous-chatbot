"""
Workflow vectors table for reasoning pattern embeddings.
"""

from sqlalchemy import Column, Integer, Text, DateTime, Float, func, ForeignKey
from pgvector.sqlalchemy import Vector

from app.models.database import Base


class WorkflowVector(Base):
    """Workflow reasoning pattern embeddings for similar query matching."""
    
    __tablename__ = "workflow_vectors"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False, index=True)
    
    # Workflow summary
    reasoning_summary = Column(Text, nullable=False)  # Natural language summary of reasoning
    
    # Workflow embedding
    workflow_embedding = Column(Vector(384), nullable=False)  # Embedding of reasoning chain
    
    # Success metrics
    is_successful = Column(Integer, default=1)  # 1=successful, 0=failed
    confidence_score = Column(Float, default=1.0)  # Confidence in this workflow pattern
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<WorkflowVector(id={self.id}, session_id={self.session_id})>"

