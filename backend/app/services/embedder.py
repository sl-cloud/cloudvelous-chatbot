"""
Embedding service using sentence-transformers.
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer
import numpy as np

from app.config import settings


class EmbeddingService:
    """Service for generating embeddings using sentence-transformers."""
    
    def __init__(self):
        """Initialize the embedding model."""
        self.model = SentenceTransformer(settings.EMBED_MODEL)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


# Global embedder instance
_embedder_instance = None


def get_embedder() -> EmbeddingService:
    """
    Get or create the global embedder instance.
    
    Returns:
        EmbeddingService instance
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = EmbeddingService()
    return _embedder_instance

