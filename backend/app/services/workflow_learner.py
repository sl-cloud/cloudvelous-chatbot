"""
Workflow learner service for generating workflow embeddings.

This service converts reasoning chains into embeddings that can be used
to find similar past workflows and improve future retrievals.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import TrainingSession, WorkflowVector, EmbeddingLink
from app.services.embedder import get_embedder
from app.schemas.workflow import ReasoningChain, WorkflowSummary


class WorkflowLearner:
    """
    Generates workflow embeddings from reasoning chains.
    
    Workflow embeddings capture:
    - The query intent
    - Which chunks were retrieved and why
    - The reasoning pattern used
    - Success/failure status
    """
    
    def __init__(self):
        """Initialize the workflow learner."""
        self.embedder = get_embedder()
    
    def generate_reasoning_summary(self, session: TrainingSession, reasoning_chain: ReasoningChain) -> str:
        """
        Generate a natural language summary of the reasoning chain.
        
        Args:
            session: Training session from database
            reasoning_chain: Parsed reasoning chain
            
        Returns:
            Natural language summary of the workflow
        """
        # Build summary from query and retrieved chunks
        summary_parts = [
            f"Query: {reasoning_chain.query}",
            f"Retrieved {len(reasoning_chain.retrieved_chunks)} chunks from:",
        ]
        
        # Group chunks by repo
        repos = {}
        for chunk in reasoning_chain.retrieved_chunks:
            if chunk.repo_name not in repos:
                repos[chunk.repo_name] = []
            repos[chunk.repo_name].append(chunk.file_path)
        
        for repo, files in repos.items():
            summary_parts.append(f"- {repo}: {', '.join(set(files))}")
        
        # Add LLM info
        summary_parts.append(f"Generated using {reasoning_chain.llm_provider}")
        
        # Add timing info
        summary_parts.append(
            f"Total time: {reasoning_chain.total_time_ms:.0f}ms "
            f"(retrieval: {reasoning_chain.retrieval_time_ms:.0f}ms)"
        )
        
        return "\n".join(summary_parts)
    
    def create_workflow_embedding(
        self,
        db: Session,
        session_id: int,
        is_successful: bool = True,
        confidence: float = 1.0
    ) -> Optional[WorkflowVector]:
        """
        Create a workflow embedding for a training session.
        
        Args:
            db: Database session
            session_id: Training session ID
            is_successful: Whether this workflow was successful
            confidence: Confidence score for this workflow pattern
            
        Returns:
            Created WorkflowVector or None if session not found
        """
        # Get training session
        session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
        if not session:
            return None
        
        # Parse reasoning chain
        reasoning_chain = ReasoningChain(**session.reasoning_chain)
        
        # Generate reasoning summary
        reasoning_summary = self.generate_reasoning_summary(session, reasoning_chain)
        
        # Generate embedding for the reasoning summary
        workflow_embedding = self.embedder.embed_text(reasoning_summary)
        
        # Create workflow vector
        workflow_vector = WorkflowVector(
            session_id=session_id,
            reasoning_summary=reasoning_summary,
            workflow_embedding=workflow_embedding,
            is_successful=1 if is_successful else 0,
            confidence_score=confidence
        )
        
        db.add(workflow_vector)
        db.commit()
        db.refresh(workflow_vector)
        
        return workflow_vector
    
    def find_similar_workflows(
        self,
        db: Session,
        query_embedding: List[float],
        top_k: int = 3,
        min_similarity: float = 0.7,
        successful_only: bool = True
    ) -> List[WorkflowVector]:
        """
        Find similar past workflows based on query embedding.
        
        Args:
            db: Database session
            query_embedding: Query embedding vector
            top_k: Number of similar workflows to return
            min_similarity: Minimum cosine similarity threshold
            successful_only: Only return successful workflows
            
        Returns:
            List of similar workflow vectors
        """
        # Build query for similar workflows
        query = db.query(
            WorkflowVector,
            WorkflowVector.workflow_embedding.cosine_distance(query_embedding).label("distance")
        )
        
        if successful_only:
            query = query.filter(WorkflowVector.is_successful == 1)
        
        # Order by similarity (lower distance = higher similarity)
        # Filter by minimum similarity (distance = 1 - similarity)
        max_distance = 1.0 - min_similarity
        similar_workflows = query.filter(
            WorkflowVector.workflow_embedding.cosine_distance(query_embedding) <= max_distance
        ).order_by(
            WorkflowVector.workflow_embedding.cosine_distance(query_embedding)
        ).limit(top_k).all()
        
        # Return just the WorkflowVector objects
        return [wf[0] for wf in similar_workflows]
    
    def get_successful_chunk_ids(
        self,
        db: Session,
        workflow_vectors: List[WorkflowVector]
    ) -> List[int]:
        """
        Get chunk IDs from successful workflows to boost in retrieval.
        
        Args:
            db: Database session
            workflow_vectors: List of similar workflow vectors
            
        Returns:
            List of chunk IDs to boost
        """
        chunk_ids = []
        
        for wf in workflow_vectors:
            # Get embedding links for this session
            links = db.query(EmbeddingLink).filter(
                EmbeddingLink.session_id == wf.session_id
            ).all()
            
            for link in links:
                if link.was_useful is None or link.was_useful:
                    chunk_ids.append(link.chunk_id)
        
        return list(set(chunk_ids))  # Remove duplicates


# Global learner instance
_learner_instance = None


def get_workflow_learner() -> WorkflowLearner:
    """
    Get or create the global workflow learner instance.
    
    Returns:
        WorkflowLearner instance
    """
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = WorkflowLearner()
    return _learner_instance

