from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LLMPort(ABC):
    """Port (interface) for Large Language Model services."""
    
    @abstractmethod
    async def generate_response_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming text response from a prompt.
        
        Args:
            prompt: Input prompt for the LLM
            
        Yields:
            Chunks of generated text
        """
        pass