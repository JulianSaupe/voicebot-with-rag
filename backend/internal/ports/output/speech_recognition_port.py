from abc import ABC, abstractmethod
from typing import AsyncGenerator

from backend.internal.domain.models.audio_transcription import AudioTranscription


class SpeechRecognitionPort(ABC):
    """Port (interface) for speech recognition services."""
    
    @abstractmethod
    async def transcribe_audio(self, audio_data: bytes, language_code: str = "de-DE") -> AudioTranscription:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes
            language_code: Language code for transcription
            
        Returns:
            AudioTranscription domain model
        """
        pass
    
    @abstractmethod
    async def transcribe_audio_stream(self, audio_stream: AsyncGenerator[bytes, None], 
                                    language_code: str = "de-DE") -> AsyncGenerator[AudioTranscription, None]:
        """
        Transcribe streaming audio data to text.
        
        Args:
            audio_stream: Stream of audio bytes
            language_code: Language code for transcription
            
        Yields:
            AudioTranscription domain models
        """
        pass