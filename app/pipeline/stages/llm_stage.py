from typing import Any

from app.llm.llm_provider import LLMProvider
from app.llm.prompt_builder import PromptBuilder
from app.pipeline.pipeline_calls import LLMStageCall
from app.pipeline.stages.stage import Stage


class LLMStage(Stage):
    def __init__(self, llm: LLMProvider, prompt_builder: PromptBuilder):
        self.llm = llm
        self.prompt_builder = prompt_builder

    def __call__(self, data: LLMStageCall) -> Any:
        prompt = self.prompt_builder.build_with_context(data.context, data.user_prompt)

        return self.llm.generate_stream(prompt=prompt)
