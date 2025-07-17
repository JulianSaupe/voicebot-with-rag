from abc import ABC, abstractmethod
from typing import AsyncGenerator

from backend.internal.domain.models.audio_transcription import AudioTranscription
from backend.internal.domain.models.voice_response import VoiceResponse


class VoicebotUseCasePort(ABC):
    """Input port (driving port) for voicebot use cases."""
    
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
    async def generate_voice_response(self, prompt: str, voice: str = None) -> VoiceResponse:
        """
        Generate a complete voice response from a text prompt.
        
        Args:
            prompt: Input prompt for the voicebot
            voice: Voice settings for TTS
            
        Returns:
            VoiceResponse domain model
        """
        pass
    
    @abstractmethod
    async def generate_streaming_voice_response(self, prompt: str, voice: str = None) -> AsyncGenerator[bytes, None]:
        """
        Generate a streaming voice response from a text prompt.
        
        Args:
            prompt: Input prompt for the voicebot
            voice: Voice settings for TTS
            
        Yields:
            Audio data chunks as bytes
        """
        pass