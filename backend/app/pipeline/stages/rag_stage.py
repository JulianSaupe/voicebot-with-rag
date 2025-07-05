from backend.app.pipeline.pipeline_calls import RAGStageCall, LLMStageCall
from backend.app.pipeline.stages.stage import Stage
from backend.app.rag.embedding_calculator import EmbeddingCalculator
from backend.app.rag.vector_database import VectorDatabase


class RAGStage(Stage):
    def __init__(self, vector_db: VectorDatabase, embedding_calculator: EmbeddingCalculator):
        self.vector_db = vector_db
        self.embedding_calculator = embedding_calculator

    def __call__(self, data: RAGStageCall) -> LLMStageCall:
        return LLMStageCall(user_prompt=data.prompt, context=[])