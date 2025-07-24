from abc import ABC, abstractmethod
from typing import List

import numpy as np

from backend.internal.ports.output.embedding_calculator import EmbeddingCalculator


class VectorDatabase(ABC):
    def __init__(self, embedding_calculator: EmbeddingCalculator, min_similarity: float = 0.5):
        self.embedding_calculator = embedding_calculator
        self.min_similarity = min_similarity

    @abstractmethod
    def create_table(self) -> None:
        """Create a table to store documents."""

    @abstractmethod
    def insert_document(self, text: str) -> None:
        """Insert document into vector database."""

    @abstractmethod
    def search(self, query: np.ndarray, top_k: int = 10) -> List[str]:
        """Search documents in vector database."""
