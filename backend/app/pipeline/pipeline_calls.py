from abc import ABC
from dataclasses import dataclass
from typing import List, Iterable


@dataclass
class StageCall(ABC):
    pass


@dataclass
class RAGStageCall(StageCall):
    prompt: str


@dataclass
class LLMStageCall(StageCall):
    user_prompt: str
    context: List[str]


@dataclass
class TTSStageCall(StageCall):
    text_stream: Iterable[str]
