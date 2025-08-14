from abc import ABC, abstractmethod
from typing import AsyncGenerator


class TTSPort(ABC):
    """Port (interface) for Text-to-Speech services."""
    
    @abstractmethod
    async def synthesize_speech_stream(self, text_stream: AsyncGenerator[str, None], 
                                     voice: str) -> AsyncGenerator[bytes, None]:
        """
        Synthesize speech from streaming text.
        
        Args:
            text_stream: Stream of text chunks
            voice: Voice settings/identifier
            
        Yields:
            Audio data chunks as bytes
        """
        pass