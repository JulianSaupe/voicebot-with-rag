from sentence_transformers import SentenceTransformer
from functools import lru_cache

from backend.internal.ports.output.embedding_calculator import EmbeddingCalculator
from numpy import ndarray


class AllMPNetBaseV2(EmbeddingCalculator):
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            print("🧠 Loading sentence transformer model (one-time initialization)...")
            cls._model = SentenceTransformer("all-mpnet-base-v2")
            print("✅ Model loaded successfully")
        return cls._instance

    def __init__(self):
        # Prevent re-initialization
        pass

    @lru_cache(maxsize=128)
    def calculate_embeddings(self, text: str) -> ndarray:
        return self._model.encode(text, normalize_embeddings=True)
