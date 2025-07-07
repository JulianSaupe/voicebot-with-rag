from backend.app.rag.embedding_calculator import EmbeddingCalculator
from sentence_transformers import SentenceTransformer


class AllMPNetBaseV2(EmbeddingCalculator):
    def __init__(self):
        self.model = SentenceTransformer("all-mpnet-base-v2")

    def calculate_embeddings(self, text: str):
        return self.model.encode(text, normalize_embeddings=True)
