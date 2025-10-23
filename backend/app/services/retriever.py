"""
Retrieval service for pgvector embedding search.

Performs semantic search over knowledge chunks using pgvector.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import KnowledgeChunk
from app.services.embedder import get_embedder
from app.config import settings


class RetrievalResult:
    """Result from a retrieval operation."""
    
    def __init__(
        self,
        chunk: KnowledgeChunk,
        similarity_score: float,
        rank_position: int
    ):
        self.chunk = chunk
        self.similarity_score = similarity_score
        self.rank_position = rank_position
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk.id,
            "repo_name": self.chunk.repo_name,
            "file_path": self.chunk.file_path,
            "section_title": self.chunk.section_title,
            "content": self.chunk.content,
            "similarity_score": self.similarity_score,
            "rank_position": self.rank_position,
            "accuracy_weight": self.chunk.accuracy_weight,
        }


class RetrieverService:
    """Service for retrieving relevant knowledge chunks."""
    
    def __init__(self):
        """Initialize the retriever service."""
        self.embedder = get_embedder()
    
    def retrieve(
        self,
        db: Session,
        query: str,
        top_k: Optional[int] = None,
        boost_chunk_ids: Optional[List[int]] = None,
        boost_factor: Optional[float] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant knowledge chunks for a query.
        
        Args:
            db: Database session
            query: User query text
            top_k: Number of chunks to retrieve (default from settings)
            boost_chunk_ids: Optional list of chunk IDs to boost in ranking
            boost_factor: Factor to boost specified chunks (default from settings)
            
        Returns:
            List of RetrievalResult objects ordered by relevance
        """
        if top_k is None:
            top_k = settings.TOP_K_RETRIEVAL
        
        if boost_factor is None:
            boost_factor = settings.WORKFLOW_BOOST_FACTOR
        
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Perform vector similarity search with accuracy weights
        # Using cosine distance (lower is more similar)
        results = db.query(
            KnowledgeChunk,
            (1.0 - KnowledgeChunk.embedding.cosine_distance(query_embedding)).label("similarity")
        ).order_by(
            KnowledgeChunk.embedding.cosine_distance(query_embedding)
        ).limit(top_k * 2).all()  # Get extra results for boosting
        
        # Convert to RetrievalResult objects with accuracy weighting
        retrieval_results = []
        for idx, (chunk, similarity) in enumerate(results):
            # Apply accuracy weight to similarity score
            weighted_score = similarity * chunk.accuracy_weight
            
            # Apply workflow boost if applicable
            if boost_chunk_ids and chunk.id in boost_chunk_ids:
                weighted_score *= boost_factor
            
            retrieval_results.append((chunk, weighted_score, similarity))
        
        # Re-sort by weighted score and take top_k
        retrieval_results.sort(key=lambda x: x[1], reverse=True)
        retrieval_results = retrieval_results[:top_k]
        
        # Create RetrievalResult objects with rank positions
        final_results = []
        for rank, (chunk, weighted_score, original_similarity) in enumerate(retrieval_results, 1):
            final_results.append(
                RetrievalResult(
                    chunk=chunk,
                    similarity_score=original_similarity,  # Store original similarity
                    rank_position=rank
                )
            )
        
        return final_results
    
    def retrieve_by_embedding(
        self,
        db: Session,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        boost_chunk_ids: Optional[List[int]] = None,
        boost_factor: Optional[float] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant knowledge chunks using a pre-computed embedding.
        
        Args:
            db: Database session
            query_embedding: Pre-computed query embedding
            top_k: Number of chunks to retrieve (default from settings)
            boost_chunk_ids: Optional list of chunk IDs to boost in ranking
            boost_factor: Factor to boost specified chunks (default from settings)
            
        Returns:
            List of RetrievalResult objects ordered by relevance
        """
        if top_k is None:
            top_k = settings.TOP_K_RETRIEVAL
        
        if boost_factor is None:
            boost_factor = settings.WORKFLOW_BOOST_FACTOR
        
        # Perform vector similarity search with accuracy weights
        results = db.query(
            KnowledgeChunk,
            (1.0 - KnowledgeChunk.embedding.cosine_distance(query_embedding)).label("similarity")
        ).order_by(
            KnowledgeChunk.embedding.cosine_distance(query_embedding)
        ).limit(top_k * 2).all()
        
        # Convert to RetrievalResult objects with accuracy weighting
        retrieval_results = []
        for idx, (chunk, similarity) in enumerate(results):
            # Apply accuracy weight to similarity score
            weighted_score = similarity * chunk.accuracy_weight
            
            # Apply workflow boost if applicable
            if boost_chunk_ids and chunk.id in boost_chunk_ids:
                weighted_score *= boost_factor
            
            retrieval_results.append((chunk, weighted_score, similarity))
        
        # Re-sort by weighted score and take top_k
        retrieval_results.sort(key=lambda x: x[1], reverse=True)
        retrieval_results = retrieval_results[:top_k]
        
        # Create RetrievalResult objects with rank positions
        final_results = []
        for rank, (chunk, weighted_score, original_similarity) in enumerate(retrieval_results, 1):
            final_results.append(
                RetrievalResult(
                    chunk=chunk,
                    similarity_score=original_similarity,
                    rank_position=rank
                )
            )
        
        return final_results


# Global retriever instance
_retriever_instance = None


def get_retriever() -> RetrieverService:
    """
    Get or create the global retriever instance.
    
    Returns:
        RetrieverService instance
    """
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = RetrieverService()
    return _retriever_instance

