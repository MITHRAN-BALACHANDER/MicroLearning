"""
Utility functions for embeddings and text processing
"""
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger


class EmbeddingManager:
    """Manage text embeddings for RAG"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        logger.info(f"Initialized embedding model: {model_name}")
    
    def encode_text(self, text: str) -> List[float]:
        """Encode single text to embedding"""
        return self.model.encode(text).tolist()
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts to embeddings"""
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)
        
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        return dot_product / (norm1 * norm2)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < text_length:
            for i in range(end, start + chunk_size // 2, -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


def extract_key_concepts(text: str, max_concepts: int = 10) -> List[str]:
    """
    Extract key concepts from text (simple keyword extraction)
    
    Args:
        text: Text to analyze
        max_concepts: Maximum number of concepts to extract
        
    Returns:
        List of key concepts
    """
    # This is a simple implementation
    # In production, use more sophisticated NLP techniques
    
    import re
    from collections import Counter
    
    # Remove special characters and convert to lowercase
    text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split into words
    words = text_clean.split()
    
    # Filter out common words (simple stopwords)
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
                 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their'}
    
    # Filter words
    filtered_words = [w for w in words if w not in stopwords and len(w) > 3]
    
    # Count frequencies
    word_freq = Counter(filtered_words)
    
    # Get top concepts
    concepts = [word for word, count in word_freq.most_common(max_concepts)]
    
    return concepts
