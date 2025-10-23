"""
Approved questions table for RAG whitelist.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from pgvector.sqlalchemy import Vector

from app.models.database import Base


class ApprovedQuestion(Base):
    """Approved questions that the chatbot can answer."""
    
    __tablename__ = "approved_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False, unique=True)
    category = Column(String(100), nullable=True, index=True)
    embedding = Column(Vector(384), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ApprovedQuestion(id={self.id}, question='{self.question[:50]}...')>"

