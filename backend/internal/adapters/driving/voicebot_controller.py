from fastapi import HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import json
import asyncio
import numpy as np
from typing import AsyncGenerator, Optional

from backend.internal.application.voicebot_service import VoicebotService
from backend.internal.domain.services.voice_activity_detector_service import VoiceActivityDetector


class VoicebotController:
    """Web controller for voicebot endpoints using hexagonal architecture."""

    def __init__(self, voicebot_service: VoicebotService):
        self.voicebot_service = voicebot_service

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

    async def transcribe_audio_websocket(self, websocket: WebSocket):
        """
        Handle WebSocket connection for real-time audio transcription with VAD.
        
        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        print("🔌 WebSocket connection established for VAD-based audio transcription")

        # Initialize VAD service for this connection
        vad = VoiceActivityDetector()

        try:
            while True:
                try:
                    # Receive JSON message from WebSocket
                    message = await websocket.receive_text()
                    data = json.loads(message)

                    if data['type'] == 'pcm':
                        # Convert array back to numpy array for PCM data
                        pcm_data = np.array(data['data'], dtype=np.float32)

                        # Process through VAD using PCM data only
                        should_transcribe, accumulated_audio = vad.process_audio_chunk(pcm_data)

                        if should_transcribe and accumulated_audio is not None and len(accumulated_audio) > 0:
                            try:
                                # Transcribe the accumulated audio directly
                                transcription = await self.voicebot_service.transcribe_audio(
                                    accumulated_audio, language_code="de-DE"
                                )

                                # Send transcription result back via WebSocket
                                if transcription.text and len(transcription.text.strip()) > 1:
                                    result = {
                                        "transcription": transcription.text,
                                        "confidence": transcription.confidence,
                                        "language_code": transcription.language_code,
                                        "status": "success"
                                    }

                                    print(f"🎤 VAD-based transcription: {transcription.text}")
                                    await websocket.send_text(json.dumps(result))

                            except Exception as e:
                                print(f"❌ Transcription error: {e}")
                                error_result = {
                                    "error": f"Transcription failed: {str(e)}",
                                    "status": "error"
                                }
                                await websocket.send_text(json.dumps(error_result))

                except WebSocketDisconnect:
                    print("🔌 WebSocket disconnected during audio streaming")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON received: {e}")
                    continue
                except Exception as e:
                    print(f"❌ Error processing audio chunk: {e}")
                    continue

            # Process any remaining buffered audio when connection closes
            final_audio = vad.force_process_buffer()
            if final_audio:
                print("🎤 Processing final buffered audio")
                try:
                    final_transcription = await self.voicebot_service.transcribe_audio(
                        final_audio, language_code="de-DE"
                    )
                    if final_transcription.text and len(final_transcription.text.strip()) > 1:
                        result = {
                            "transcription": final_transcription.text,
                            "confidence": final_transcription.confidence,
                            "language_code": final_transcription.language_code,
                            "status": "success"
                        }
                        await websocket.send_text(json.dumps(result))
                except Exception as e:
                    print(f"❌ Failed to transcribe final audio: {e}")

        except WebSocketDisconnect:
            print("🔌 WebSocket disconnected")
        except Exception as e:
            print(f"❌ Error in WebSocket audio transcription: {e}")
            import traceback
            traceback.print_exc()

            # Try to send error message if connection is still open
            try:
                error_result = {
                    "error": str(e),
                    "status": "error"
                }
                await websocket.send_text(json.dumps(error_result))
            except:
                pass  # Connection might be closed
