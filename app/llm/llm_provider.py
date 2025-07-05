from abc import abstractmethod, ABC


class LLMProvider(ABC):
    @abstractmethod
    def generate_stream(self, prompt: str):
        """Generate stream from LLM."""
