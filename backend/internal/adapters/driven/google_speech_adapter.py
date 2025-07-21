from typing import AsyncGenerator
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import numpy as np

from google.cloud import speech

from backend.internal.ports.output.speech_recognition_port import SpeechRecognitionPort
from backend.internal.domain.models.audio_transcription import AudioTranscription


class GoogleSpeechAdapter(SpeechRecognitionPort):
    """Adapter for Google Cloud Speech-to-Text service."""

    def __init__(self):
        self.client = speech.SpeechClient()
        self.executor = ThreadPoolExecutor(max_workers=4)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def transcribe_audio(self, audio_data: np.ndarray, language_code: str = "de-DE") -> AudioTranscription:
        """Transcribe audio data using Google Cloud Speech-to-Text."""
        try:
            # Convert PCM numpy array to 16-bit PCM bytes
            # Ensure audio is in the correct range [-1, 1] and convert to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            audio_bytes = audio_int16.tobytes()

            # Configure the speech recognition for PCM audio - optimized for speed
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=48000,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model="latest_short",  # Faster model for shorter audio segments
                enable_word_time_offsets=False,  # Disable to reduce processing time
                max_alternatives=1,
                use_enhanced=True,
            )

            # Create audio object
            audio = speech.RecognitionAudio(content=audio_bytes)

            # Create a partial function with keyword arguments
            recognize_func = partial(
                self.client.recognize,
                config=config,
                audio=audio
            )

            # Run the synchronous Google Speech API call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                recognize_func
            )

            # Process the response
            transcription_text = ""
            confidence = 0.0

            if response.results:
                for result in response.results:
                    if result.alternatives:
                        transcription_text = result.alternatives[0].transcript.strip()
                        confidence = result.alternatives[0].confidence if result.alternatives[0].confidence else 0.0
                        break  # Take the first (best) result

            self.logger.info(f"Transcription completed: '{transcription_text}' (confidence: {confidence:.2f})")

            return AudioTranscription(
                text=transcription_text,
                confidence=confidence,
                language_code=language_code
            )

        except Exception as e:
            self.logger.error(f"Error in Google Speech transcription: {e}")
            raise RuntimeError(f"Speech transcription failed: {str(e)}")
