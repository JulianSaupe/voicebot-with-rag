from abc import ABC
from dataclasses import dataclass
from typing import List


@dataclass
class StageCall(ABC):
    pass


@dataclass
class RAGStageCall(StageCall):
    user_prompt: str


@dataclass
class LLMStageCall(StageCall):
    user_prompt: str
    context: List[str]
