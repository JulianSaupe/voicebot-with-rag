from abc import ABC, abstractmethod
from typing import List

import numpy as np


class RAGPort(ABC):
    """Port (interface) for Retrieval-Augmented Generation services."""
    
    @abstractmethod
    async def retrieve_relevant_documents(self, query: str, max_results: int = 5) -> List[str]:
        """
        Retrieve relevant documents for a given query.
        
        Args:
            query: Search query
            max_results: Maximum number of documents to retrieve
            
        Returns:
            List of relevant document contents
        """
        pass
    
    @abstractmethod
    async def calculate_embeddings(self, text: str) -> np.ndarray:
        """
        Calculate embeddings for a given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Vector embeddings as list of floats
        """
        pass