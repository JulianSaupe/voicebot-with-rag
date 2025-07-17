from dataclasses import dataclass
from typing import AsyncGenerator, Optional


@dataclass
class VoiceResponse:
    """Domain model representing a voice response from the system."""
    text_content: str
    voice_settings: str
    audio_stream: Optional[AsyncGenerator[bytes, None]] = None
    
    def has_content(self) -> bool:
        """Check if the response has meaningful content."""
        return bool(self.text_content and self.text_content.strip())
    
    def get_content_length(self) -> int:
        """Get the length of the text content."""
        return len(self.text_content) if self.text_content else 0
    
    def is_streaming(self) -> bool:
        """Check if this response includes an audio stream."""
        return self.audio_stream is not None