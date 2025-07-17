from abc import abstractmethod, ABC

import numpy as np


class EmbeddingCalculator(ABC):
    @abstractmethod
    def calculate_embeddings(self, text: str) -> np.ndarray:
        """Calculate embedding for given text."""
