from typing import AsyncGenerator

from google.cloud import speech

from backend.internal.ports.output.speech_recognition_port import SpeechRecognitionPort
from backend.internal.domain.models.audio_transcription import AudioTranscription


class GoogleSpeechAdapter(SpeechRecognitionPort):
    """Adapter for Google Cloud Speech-to-Text service."""
    
    def __init__(self):
        self.client = speech.SpeechClient()
    
    async def transcribe_audio(self, audio_data: bytes, language_code: str = "de-DE") -> AudioTranscription:
        """Transcribe audio data using Google Cloud Speech-to-Text."""
        try:
            # Configure the speech recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code=language_code,
                enable_automatic_punctuation=True,
            )
            
            # Create audio object
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Perform recognition
            response = self.client.recognize(config=config, audio=audio)
            
            # Process the response
            transcription_text = ""
            confidence = None
            
            for result in response.results:
                transcription_text = result.alternatives[0].transcript
                confidence = result.alternatives[0].confidence
                break  # Take the first (best) result
            
            return AudioTranscription(
                text=transcription_text,
                confidence=confidence,
                language_code=language_code
            )
            
        except Exception as e:
            print(f"❌ Error in Google Speech transcription: {e}")
            raise RuntimeError(f"Speech transcription failed: {str(e)}")
    
    async def transcribe_audio_stream(self, audio_stream: AsyncGenerator[bytes, None], 
                                    language_code: str = "de-DE") -> AsyncGenerator[AudioTranscription, None]:
        """Transcribe streaming audio data using Google Cloud Speech-to-Text."""
        try:
            # Configure the speech recognition for streaming
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code=language_code,
                enable_automatic_punctuation=True,
            )
            
            streaming_config = speech.StreamingRecognitionConfig(
                config=config,
                interim_results=True,
            )
            
            # Create streaming request generator
            async def request_generator():
                yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
                async for audio_chunk in audio_stream:
                    yield speech.StreamingRecognizeRequest(audio_content=audio_chunk)
            
            # Perform streaming recognition
            responses = self.client.streaming_recognize(request_generator())
            
            for response in responses:
                for result in response.results:
                    if result.is_final:
                        yield AudioTranscription(
                            text=result.alternatives[0].transcript,
                            confidence=result.alternatives[0].confidence,
                            language_code=language_code
                        )
                        
        except Exception as e:
            print(f"❌ Error in Google Speech streaming transcription: {e}")
            raise RuntimeError(f"Streaming speech transcription failed: {str(e)}")