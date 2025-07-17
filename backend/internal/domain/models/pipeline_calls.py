from abc import ABC
from dataclasses import dataclass
from typing import List, Iterable


@dataclass
class StageCall(ABC):
    pass


@dataclass
class RAGStageCall(StageCall):
    prompt: str
    voice: str = "de-DE-Chirp3-HD-Charon"


@dataclass
class LLMStageCall(StageCall):
    user_prompt: str
    context: List[str]
    voice: str = "de-DE-Chirp3-HD-Charon"


@dataclass
class TTSStageCall(StageCall):
    text_stream: Iterable[str]
    voice: str = "de-DE-Chirp3-HD-Charon"
