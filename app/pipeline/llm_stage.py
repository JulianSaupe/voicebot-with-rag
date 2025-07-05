from typing import Any

from app.llm.llm_provider import LLMProvider
from app.pipeline.stage import Stage


class LLMStage(Stage):
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def __call__(self, data: Any) -> Any:
        pass
