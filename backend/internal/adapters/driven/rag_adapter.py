from typing import List

import numpy as np

from backend.internal.ports.output.rag_port import RAGPort
from backend.internal.ports.output.embedding_calculator import EmbeddingCalculator
from backend.internal.ports.output.vector_database import VectorDatabase


class RAGAdapter(RAGPort):
    """Adapter for RAG (Retrieval-Augmented Generation) system."""
    
    def __init__(self, embedding_calculator: EmbeddingCalculator, vector_db: VectorDatabase):
        self.embedding_calculator = embedding_calculator
        self.vector_db = vector_db
    
    async def retrieve_relevant_documents(self, query: str, max_results: int = 5) -> List[str]:
        """Retrieve relevant documents for a given query using vector similarity search."""
        try:
            # Calculate embeddings for the query
            query_embeddings = self.embedding_calculator.calculate_embeddings(query)

            # Search for similar documents in the vector database
            return self.vector_db.search(query_embeddings, max_results)
            
        except Exception as e:
            print(f"❌ Error in RAG document retrieval: {e}")
            # Return empty list on error to allow conversation to continue
            return []
    
    async def calculate_embeddings(self, text: str) -> np.ndarray:
        """Calculate embeddings for a given text."""
        try:
            embeddings = self.embedding_calculator.calculate_embeddings(text)
            return embeddings
            
        except Exception as e:
            print(f"❌ Error in embedding calculation: {e}")
            raise RuntimeError(f"Embedding calculation failed: {str(e)}")