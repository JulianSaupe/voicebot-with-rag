from app.llm.gemini import Gemini
from app.llm.prompt_builder import PromptBuilder
from app.pipeline.stages.llm_stage import LLMStage
from app.pipeline.pipeline import Pipeline
from app.pipeline.stages.rag_stage import RAGStage
from app.rag.postgres_db import PostgresVectorDB

if __name__ == "__main__":
    prompt = "Erkläre was AI ist"
    task_description = ""

    llm = Gemini()
    vector_db = PostgresVectorDB(llm)

    rag_stage = RAGStage(embedding_calculator=llm, vector_db=vector_db)
    llm_stage = LLMStage(llm=llm, prompt_builder=PromptBuilder(task_description))

    pipeline = Pipeline(stages=[rag_stage, llm_stage])
