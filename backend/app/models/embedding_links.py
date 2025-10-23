"""
Embedding links junction table connecting training sessions and knowledge chunks.
"""

from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, func

from app.models.database import Base


class EmbeddingLink(Base):
    """Junction table linking training sessions to knowledge chunks with feedback."""
    
    __tablename__ = "embedding_links"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False, index=True)
    chunk_id = Column(Integer, ForeignKey("knowledge_chunks.id"), nullable=False, index=True)
    
    # Retrieval metadata
    similarity_score = Column(Float, nullable=False)  # Cosine similarity at retrieval time
    rank_position = Column(Integer, nullable=False)  # Position in retrieval results (1-based)
    
    # Feedback
    was_useful = Column(Boolean, nullable=True)  # NULL=no feedback, True=useful, False=not useful
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<EmbeddingLink(session_id={self.session_id}, chunk_id={self.chunk_id}, score={self.similarity_score})>"

