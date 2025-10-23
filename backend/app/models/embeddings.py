"""
Knowledge chunks table for RAG embeddings.
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func
from pgvector.sqlalchemy import Vector

from app.models.database import Base


class KnowledgeChunk(Base):
    """Knowledge chunks with embeddings for RAG retrieval."""
    
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    repo_name = Column(String(255), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    section_title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)  # Dimension for all-MiniLM-L6-v2
    accuracy_weight = Column(Float, default=1.0, nullable=False)  # Phase 1 addition
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<KnowledgeChunk(id={self.id}, repo={self.repo_name}, file={self.file_path})>"

