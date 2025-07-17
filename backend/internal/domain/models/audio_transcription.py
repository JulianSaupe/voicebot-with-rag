from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioTranscription:
    """Domain model representing a transcribed audio input."""
    text: str
    confidence: Optional[float] = None
    language_code: Optional[str] = None
    
    def is_empty(self) -> bool:
        """Check if the transcription is empty or contains only whitespace."""
        return not self.text or self.text.strip() == ""
    
    def get_clean_text(self) -> str:
        """Get the transcription text with leading/trailing whitespace removed."""
        return self.text.strip()