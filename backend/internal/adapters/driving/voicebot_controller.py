from fastapi import HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from backend.internal.application.voicebot_service import VoicebotService


class VoicebotController:
    """Web controller for voicebot endpoints using hexagonal architecture."""

    def __init__(self, voicebot_service: VoicebotService):
        self.voicebot_service = voicebot_service

    async def transcribe_audio(self, request: Request):
        """
        Transcribe audio from request body.
        
        Args:
            request: FastAPI request containing audio data
            
        Returns:
            Dictionary with transcription result
        """
        try:
            # Read audio data from request
            audio_data = await request.body()
            print(f"🎤 Received audio data: {len(audio_data)} bytes")

            # Use the voicebot service to transcribe
            transcription = await self.voicebot_service.transcribe_audio(audio_data)

            print(f"🎤 Transcription: {transcription.text}")

            return {
                "transcription": transcription.text,
                "confidence": transcription.confidence,
                "language_code": transcription.language_code,
                "status": "success"
            }

        except ValueError as e:
            print(f"❌ Validation error in speech transcription: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            print(f"❌ Error in speech transcription: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    async def get_audio_stream(self, prompt: str = Query(..., description="The prompt to generate audio for"),
                               voice: str = Query("de-DE-Chirp3-HD-Charon", description="The voice to use for TTS")):
        """
        Stream audio response for a given prompt.
        
        Args:
            prompt: Input prompt for the voicebot
            voice: Voice settings for TTS
            
        Returns:
            StreamingResponse with audio data
        """
        try:
            # Generate streaming audio response using the voicebot service
            audio_stream = self.voicebot_service.generate_streaming_voice_response(prompt, voice)

            return StreamingResponse(
                audio_stream,
                media_type="audio/pcm",
                headers={
                    "Content-Disposition": "attachment; filename=response.pcm",
                    "Sample-Rate": "24000",
                    "Channels": "1",
                    "Sample-Format": "int16"
                }
            )

        except Exception as e:
            print(f"❌ Error in audio stream generation: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    async def get_text_response(self, prompt: str = Query(..., description="The prompt to generate response for"),
                                voice: str = Query("de-DE-Chirp3-HD-Charon", description="The voice to use for TTS")):
        """
        Get text response for a given prompt (non-streaming).
        
        Args:
            prompt: Input prompt for the voicebot
            voice: Voice settings for TTS
            
        Returns:
            Dictionary with text response
        """
        try:
            # Generate voice response using the voicebot service
            response = await self.voicebot_service.generate_voice_response(prompt, voice)

            return {
                "text": response.text_content,
                "voice_settings": response.voice_settings,
                "content_length": response.get_content_length(),
                "status": "success"
            }

        except Exception as e:
            print(f"❌ Error in text response generation: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
