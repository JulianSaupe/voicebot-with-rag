from abc import abstractmethod, ABC


class EmbeddingCalculator(ABC):
    @abstractmethod
    def calculate_embeddings(self, text: str):
        """Calculate embedding for given text."""
