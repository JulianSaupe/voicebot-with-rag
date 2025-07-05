from app.pipeline.pipeline_calls import RAGStageCall, LLMStageCall
from app.pipeline.stages.stage import Stage
from app.rag.embedding_calculator import EmbeddingCalculator
from app.rag.vector_database import VectorDatabase


class RAGStage(Stage):
    def __init__(self, vector_db: VectorDatabase, embedding_calculator: EmbeddingCalculator):
        self.vector_db = vector_db
        self.embedding_calculator = embedding_calculator

    def __call__(self, data: RAGStageCall) -> LLMStageCall:
        pass