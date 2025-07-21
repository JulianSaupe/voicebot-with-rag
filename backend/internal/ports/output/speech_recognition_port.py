from abc import ABC, abstractmethod
from typing import AsyncGenerator
import numpy as np

from backend.internal.domain.models.audio_transcription import AudioTranscription


class SpeechRecognitionPort(ABC):
    """Port (interface) for speech recognition services."""
    
    @abstractmethod
    async def transcribe_audio(self, audio_data: np.ndarray, language_code: str = "de-DE") -> AudioTranscription:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw PCM audio data as numpy array
            language_code: Language code for transcription
            
        Returns:
            AudioTranscription domain model
        """
        pass