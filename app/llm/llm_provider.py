from abc import abstractmethod, ABC
from typing import Iterable


class LLMProvider(ABC):
    @abstractmethod
    def generate_text_stream(self, prompt: str) -> Iterable:
        """Generate text stream from LLM."""
