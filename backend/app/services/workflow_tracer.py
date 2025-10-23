"""
Workflow tracer service for capturing complete reasoning chains.

This service captures every step of the RAG pipeline for training and analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from app.schemas.workflow import WorkflowStep, ReasoningChain, RetrievedChunkTrace


class WorkflowTracer:
    """
    Captures complete reasoning chains for RAG workflows.
    
    Tracks:
    - Query processing and embedding
    - Retrieved chunks with scores
    - Workflow context (repo relationships)
    - LLM generation details
    - Timing for each step
    """
    
    def __init__(self, query: str):
        """
        Initialize workflow tracer for a query.
        
        Args:
            query: The user's question
        """
        self.query = query
        self.start_time = time.time()
        
        # Timing tracking
        self.query_embedding_time_ms: float = 0.0
        self.retrieval_time_ms: float = 0.0
        self.generation_time_ms: float = 0.0
        
        # Workflow steps
        self.steps: List[WorkflowStep] = []
        
        # Retrieved chunks
        self.retrieved_chunks: List[RetrievedChunkTrace] = []
        
        # Workflow context
        self.workflow_context: Optional[Dict[str, Any]] = None
        
        # LLM metadata
        self.llm_provider: str = ""
        self.llm_model: Optional[str] = None
    
    def start_step(self, step_name: str) -> float:
        """
        Start timing a workflow step.
        
        Args:
            step_name: Name of the step (e.g., "query_embedding")
            
        Returns:
            Start time for the step
        """
        return time.time()
    
    def end_step(self, step_name: str, start_time: float, metadata: Optional[Dict[str, Any]] = None):
        """
        End timing a workflow step and record it.
        
        Args:
            step_name: Name of the step
            start_time: Start time from start_step()
            metadata: Optional metadata about the step
        """
        duration_ms = (time.time() - start_time) * 1000
        
        step = WorkflowStep(
            step_name=step_name,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        self.steps.append(step)
        
        # Update specific timing fields
        if step_name == "query_embedding":
            self.query_embedding_time_ms = duration_ms
        elif step_name == "retrieval":
            self.retrieval_time_ms = duration_ms
        elif step_name == "generation":
            self.generation_time_ms = duration_ms
    
    def add_retrieved_chunk(
        self,
        chunk_id: int,
        repo_name: str,
        file_path: str,
        section_title: Optional[str],
        content: str,
        similarity_score: float,
        rank_position: int,
        accuracy_weight: float
    ):
        """
        Add a retrieved chunk to the trace.
        
        Args:
            chunk_id: Database ID of the chunk
            repo_name: Repository name
            file_path: File path within repo
            section_title: Optional section title
            content: Full content (will be truncated for preview)
            similarity_score: Cosine similarity score
            rank_position: Position in retrieval results (1-based)
            accuracy_weight: Current accuracy weight of the chunk
        """
        chunk_trace = RetrievedChunkTrace(
            chunk_id=chunk_id,
            repo_name=repo_name,
            file_path=file_path,
            section_title=section_title,
            content_preview=content[:200] + ("..." if len(content) > 200 else ""),
            similarity_score=similarity_score,
            rank_position=rank_position,
            accuracy_weight=accuracy_weight
        )
        self.retrieved_chunks.append(chunk_trace)
    
    def set_workflow_context(self, context: Dict[str, Any]):
        """
        Set workflow context (e.g., repo relationships).
        
        Args:
            context: Workflow context dictionary
        """
        self.workflow_context = context
    
    def set_llm_info(self, provider: str, model: Optional[str] = None):
        """
        Set LLM provider information.
        
        Args:
            provider: LLM provider name (e.g., "openai", "gemini")
            model: Optional model name
        """
        self.llm_provider = provider
        self.llm_model = model
    
    def build_reasoning_chain(self) -> ReasoningChain:
        """
        Build the complete reasoning chain.
        
        Returns:
            ReasoningChain object with all captured information
        """
        total_time_ms = (time.time() - self.start_time) * 1000
        
        return ReasoningChain(
            query=self.query,
            query_embedding_time_ms=self.query_embedding_time_ms,
            retrieval_time_ms=self.retrieval_time_ms,
            generation_time_ms=self.generation_time_ms,
            total_time_ms=total_time_ms,
            steps=self.steps,
            retrieved_chunks=self.retrieved_chunks,
            workflow_context=self.workflow_context,
            llm_provider=self.llm_provider,
            llm_model=self.llm_model
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert reasoning chain to dictionary for database storage.
        
        Returns:
            Dictionary representation suitable for JSON column
        """
        chain = self.build_reasoning_chain()
        return chain.model_dump(mode="json")
