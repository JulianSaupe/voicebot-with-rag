import time

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

        # Initialize VAD service for this connection with optimized parameters for faster response
        vad = VoiceActivityDetector(
            silence_threshold_ms=200,  # Reduced from 500ms to 200ms for faster response
            min_speech_duration_ms=100,  # Increased slightly to avoid false positives
            sample_rate=48000
        )

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
                                    transcription_result = {
                                        "type": "transcription",
                                        "transcription": transcription.text,
                                        "confidence": transcription.confidence,
                                        "language_code": transcription.language_code,
                                        "status": "success"
                                    }

                                    print(f"🎤 VAD-based transcription: {transcription.text}")
                                    await websocket.send_text(json.dumps(transcription_result))

                                    # Process transcription through LLM and generate audio response
                                    try:
                                        print(f"🤖 Processing transcription through LLM: {transcription.text}")

                                        # Generate streaming audio response using the voicebot service
                                        audio_stream = self.voicebot_service.generate_streaming_voice_response(
                                            transcription.text,
                                            voice="de-DE-Chirp3-HD-Charon"
                                        )

                                        # Stream audio chunks back via WebSocket, including LLM response in first chunk
                                        chunk_count = 0
                                        previous_text = None
                                        response_id = int(time.time())
                                        async for audio_chunk, text in audio_stream:
                                            # print(f"Text chunk: {text}")
                                            if audio_chunk:
                                                chunk_count += 1
                                                audio_message = {
                                                    "type": "audio",
                                                    "data": list(audio_chunk),
                                                    "chunk_number": chunk_count,
                                                    "status": "streaming",
                                                    "id": response_id,
                                                }

                                                if text != previous_text:
                                                    audio_message["llm_response"] = text

                                                previous_text = text

                                                await websocket.send_text(json.dumps(audio_message))

                                        # Send end of audio stream marker
                                        end_message = {
                                            "type": "audio_end",
                                            "total_chunks": chunk_count,
                                            "status": "complete"
                                        }
                                        await websocket.send_text(json.dumps(end_message))
                                        print(f"🔊 Audio streaming complete - sent {chunk_count} chunks")

                                    except Exception as llm_error:
                                        print(f"❌ Error in LLM processing or audio generation: {llm_error}")
                                        import traceback
                                        traceback.print_exc()

                                        error_message = {
                                            "type": "audio_error",
                                            "error": f"Failed to generate audio response: {str(llm_error)}",
                                            "status": "error"
                                        }
                                        await websocket.send_text(json.dumps(error_message))

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
                        transcription_result = {
                            "type": "transcription",
                            "transcription": final_transcription.text,
                            "confidence": final_transcription.confidence,
                            "language_code": final_transcription.language_code,
                            "status": "success"
                        }
                        await websocket.send_text(json.dumps(transcription_result))

                        # Process final transcription through LLM and generate audio response
                        try:
                            print(f"🤖 Processing final transcription through LLM: {final_transcription.text}")

                            # Generate streaming audio response using the voicebot service
                            audio_stream = self.voicebot_service.generate_streaming_voice_response(
                                final_transcription.text,
                                voice="de-DE-Chirp3-HD-Charon"
                            )

                            # Stream audio chunks back via WebSocket
                            chunk_count = 0
                            async for audio_chunk, _ in audio_stream:
                                if audio_chunk:
                                    chunk_count += 1
                                    audio_message = {
                                        "type": "audio",
                                        "data": list(audio_chunk),  # Convert bytes to list for JSON serialization
                                        "chunk_number": chunk_count,
                                        "status": "streaming"
                                    }
                                    await websocket.send_text(json.dumps(audio_message))
                                    print(f"🔊 Sent final audio chunk {chunk_count} ({len(audio_chunk)} bytes)")

                            # Send end of audio stream marker
                            end_message = {
                                "type": "audio_end",
                                "total_chunks": chunk_count,
                                "status": "complete"
                            }
                            await websocket.send_text(json.dumps(end_message))
                            print(f"🔊 Final audio streaming complete - sent {chunk_count} chunks")

                        except Exception as llm_error:
                            print(f"❌ Error in final LLM processing or audio generation: {llm_error}")
                            error_message = {
                                "type": "audio_error",
                                "error": f"Failed to generate final audio response: {str(llm_error)}",
                                "status": "error"
                            }
                            await websocket.send_text(json.dumps(error_message))

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
