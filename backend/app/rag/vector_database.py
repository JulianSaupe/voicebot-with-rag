from abc import ABC, abstractmethod

from backend.app.rag.embedding_calculator import EmbeddingCalculator


class VectorDatabase(ABC):
    def __init__(self, embedding_calculator: EmbeddingCalculator):
        self.embedding_calculator = embedding_calculator

    @abstractmethod
    def create_table(self):
        """Create a table to store documents."""

    @abstractmethod
    def insert_document(self, doc_id: str, text: str):
        """Insert document into vector database."""

    @abstractmethod
    def search(self, query: str, top_k: int = 10):
        """Search documents in vector database."""
