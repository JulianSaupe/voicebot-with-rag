from sentence_transformers import SentenceTransformer

from backend.internal.ports.output.embedding_calculator import EmbeddingCalculator
from numpy import ndarray


class AllMPNetBaseV2(EmbeddingCalculator):
    def __init__(self):
        self.model = SentenceTransformer("all-mpnet-base-v2")

    def calculate_embeddings(self, text: str) -> ndarray:
        return self.model.encode(text, normalize_embeddings=True)
