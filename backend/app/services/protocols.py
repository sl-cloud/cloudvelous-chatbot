"""
Protocol definitions for service interfaces.

These Protocol classes define the expected interfaces for services,
enabling better type checking and making it easier to create mock
implementations for testing.
"""

from typing import Protocol, List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.services.retriever import RetrievalResult
from app.models import KnowledgeChunk


class EmbedderProtocol(Protocol):
    """
    Protocol for embedding service interface.
    
    Defines the contract for any embedding service implementation.
    """
    
    dimension: int
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        ...
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        ...
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        ...


class RetrieverProtocol(Protocol):
    """
    Protocol for retrieval service interface.
    
    Defines the contract for any retrieval service implementation.
    """
    
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
        ...


class GeneratorProtocol(Protocol):
    """
    Protocol for generation service interface.
    
    Defines the contract for any generation service implementation.
    """
    
    def generate(
        self,
        query: str,
        retrieval_results: List[RetrievalResult],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate an answer using the LLM with retrieved context.
        
        Args:
            query: User's question
            retrieval_results: Retrieved knowledge chunks
            conversation_history: Optional conversation history
            
        Returns:
            Generated response text
        """
        ...


class WorkflowTracerProtocol(Protocol):
    """
    Protocol for workflow tracer interface.
    
    Defines the contract for workflow tracing implementations.
    """
    
    def start_workflow(self) -> None:
        """Start tracking a new workflow."""
        ...
    
    def add_step(
        self,
        step_name: str,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a step to the current workflow.
        
        Args:
            step_name: Name of the step
            duration_ms: Duration in milliseconds
            metadata: Optional metadata for the step
        """
        ...
    
    def get_reasoning_chain(self) -> Dict[str, Any]:
        """
        Get the complete reasoning chain for the workflow.
        
        Returns:
            Dictionary containing workflow steps and metadata
        """
        ...


class WorkflowLearnerProtocol(Protocol):
    """
    Protocol for workflow learning service interface.
    
    Defines the contract for workflow learning implementations.
    """
    
    def create_workflow_embedding(
        self,
        db: Session,
        session_id: int,
        is_successful: bool,
        confidence: float
    ) -> Optional[Any]:
        """
        Create a workflow embedding for a training session.
        
        Args:
            db: Database session
            session_id: Training session ID
            is_successful: Whether the workflow was successful
            confidence: Confidence score (0-1)
            
        Returns:
            WorkflowVector object if created, None otherwise
        """
        ...
    
    def find_similar_workflows(
        self,
        db: Session,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.7
    ) -> List[tuple]:
        """
        Find similar workflows to a query.
        
        Args:
            db: Database session
            query_embedding: Query embedding vector
            top_k: Number of similar workflows to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (workflow_vector, similarity_score) tuples
        """
        ...


class AdminServiceProtocol(Protocol):
    """
    Protocol for admin service interface.
    
    Defines the contract for admin service implementations.
    """
    
    def list_sessions(self, request: Any) -> Any:
        """
        List training sessions with filtering and pagination.
        
        Args:
            request: Session list request
            
        Returns:
            Paginated session list response
        """
        ...
    
    def submit_bulk_feedback(self, request: Any) -> Any:
        """
        Submit feedback for multiple sessions in bulk.
        
        Args:
            request: Bulk feedback request
            
        Returns:
            Bulk feedback response with results
        """
        ...
    
    def adjust_chunk_weight(self, request: Any) -> Any:
        """
        Manually adjust chunk accuracy weight.
        
        Args:
            request: Chunk weight adjustment request
            
        Returns:
            Adjustment confirmation response
        """
        ...
    
    def get_admin_stats(self) -> Any:
        """
        Get comprehensive admin statistics.
        
        Returns:
            Admin statistics response
        """
        ...


class InspectorServiceProtocol(Protocol):
    """
    Protocol for inspector service interface.
    
    Defines the contract for session inspection implementations.
    """
    
    async def inspect_session(self, session_id: int) -> Any:
        """
        Get complete embedding inspection details for a session.
        
        Args:
            session_id: Training session ID
            
        Returns:
            Complete session inspection data
        """
        ...
    
    async def compare_sessions(
        self,
        session_id_1: int,
        session_id_2: int,
        include_chunk_overlap: bool = True
    ) -> Any:
        """
        Compare two training sessions side-by-side.
        
        Args:
            session_id_1: First session ID
            session_id_2: Second session ID
            include_chunk_overlap: Whether to analyze chunk overlap
            
        Returns:
            Comparison analysis response
        """
        ...


# Type aliases for convenience
Embedder = EmbedderProtocol
Retriever = RetrieverProtocol
Generator = GeneratorProtocol
WorkflowTracer = WorkflowTracerProtocol
WorkflowLearner = WorkflowLearnerProtocol
AdminService = AdminServiceProtocol
InspectorService = InspectorServiceProtocol

