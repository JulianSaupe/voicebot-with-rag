from backend.app.llm.llm_provider import LLMProvider
from backend.app.llm.prompt_builder import PromptBuilder
from backend.app.pipeline.pipeline_calls import LLMStageCall, TTSStageCall
from backend.app.pipeline.stages.stage import Stage


class LLMStage(Stage):
    def __init__(self, llm: LLMProvider, prompt_builder: PromptBuilder):
        self.llm = llm
        self.prompt_builder = prompt_builder

    def __call__(self, data: LLMStageCall) -> TTSStageCall:
        prompt = self.prompt_builder.build_with_context(data.context, data.user_prompt)
        text_stream = self.llm.generate_text_stream(prompt=prompt)
        
        return TTSStageCall(text_stream=text_stream)