from typing import AsyncGenerator, Optional
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import numpy as np

from google.cloud import speech

from backend.internal.ports.output.speech_recognition_port import SpeechRecognitionPort
from backend.internal.domain.models.audio_transcription import AudioTranscription
from backend.internal.domain.services.async_process_manager import AsyncCancellationToken


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


class CancellableGoogleSpeechAdapter(GoogleSpeechAdapter):
    """Cancellable version of Google Speech Adapter with process cancellation support."""
    
    def __init__(self):
        super().__init__()
        self._cancellation_token: Optional[AsyncCancellationToken] = None
    
    def set_cancellation_token(self, token: AsyncCancellationToken) -> None:
        """Set the cancellation token for this adapter instance."""
        self._cancellation_token = token
    
    async def transcribe_audio(self, audio_data: np.ndarray, language_code: str = "de-DE") -> AudioTranscription:
        """Transcribe audio data using Google Cloud Speech-to-Text with cancellation support."""
        # Check for cancellation before starting
        if self._cancellation_token and self._cancellation_token.is_cancelled():
            raise asyncio.CancelledError(f"Transcription cancelled: {self._cancellation_token.cancellation_reason}")
        
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
            api_task = loop.run_in_executor(
                self.executor,
                recognize_func
            )
            
            # If we have a cancellation token, race the API call against cancellation
            if self._cancellation_token:
                cancellation_task = asyncio.create_task(
                    self._cancellation_token.wait_for_cancellation()
                )
                
                try:
                    # Race the API call against cancellation
                    done, pending = await asyncio.wait(
                        [api_task, cancellation_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Cancel any pending tasks
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                    
                    # Check which task completed first
                    completed_task = done.pop()
                    
                    if completed_task == cancellation_task:
                        # Cancellation won the race
                        reason = await completed_task
                        self.logger.info(f"Speech transcription cancelled: {reason}")
                        raise asyncio.CancelledError(f"Transcription cancelled: {reason}")
                    else:
                        # API call completed first
                        response = await completed_task
                        
                except asyncio.CancelledError:
                    # Handle cancellation during the race
                    self.logger.info("Speech transcription cancelled during processing")
                    # Make sure to cancel the API task if it's still running
                    if not api_task.done():
                        api_task.cancel()
                        try:
                            await api_task
                        except asyncio.CancelledError:
                            pass
                    raise
            else:
                # No cancellation token, run normally
                response = await api_task

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

        except asyncio.CancelledError:
            # Re-raise cancellation errors
            raise
        except Exception as e:
            self.logger.error(f"Error in Google Speech transcription: {e}")
            raise RuntimeError(f"Speech transcription failed: {str(e)}")
