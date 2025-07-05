from abc import abstractmethod, ABC
from typing import Iterable


class LLMProvider(ABC):
    @abstractmethod
    def generate_stream(self, prompt: str) -> Iterable:
        """Generate stream from LLM."""
