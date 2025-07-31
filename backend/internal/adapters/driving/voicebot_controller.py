import time

from fastapi import WebSocket, WebSocketDisconnect
import json
import numpy as np

from backend.internal.application.voicebot_service import VoicebotService
from backend.internal.application.voice_activity_detector_service import VoiceActivityDetector


class VoicebotController:
    """Web controller for voicebot endpoints using hexagonal architecture."""

    def __init__(self, voicebot_service: VoicebotService):
        self.voicebot_service = voicebot_service

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

    async def text_input_websocket(self, websocket: WebSocket):
        """
        Handle WebSocket connection for text input with audio response streaming.
        
        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        print("🔌 WebSocket connection established for text input with audio response")

        try:
            while True:
                try:
                    # Receive JSON message from WebSocket
                    message = await websocket.receive_text()
                    data = json.loads(message)

                    if data['type'] == 'text_prompt':
                        data = data['data']
                        text_input = data.get('text', '').strip()
                        voice = data.get('voice', 'de-DE-Chirp3-HD-Charon')

                        if not text_input:
                            error_message = {
                                "type": "audio_error",
                                "error": "Empty text input received",
                                "status": "error"
                            }
                            await websocket.send_text(json.dumps(error_message))
                            continue

                        print(f"🤖 Processing text input through LLM: {text_input}")

                        try:
                            # Generate streaming audio response using the voicebot service
                            audio_stream = self.voicebot_service.generate_streaming_voice_response(
                                text_input,
                                voice=voice
                            )

                            # Stream audio chunks back via WebSocket, including LLM response in first chunk
                            chunk_count = 0
                            previous_text = None
                            response_id = int(time.time())
                            async for audio_chunk, text in audio_stream:
                                if audio_chunk:
                                    chunk_count += 1
                                    audio_message = {
                                        "type": "audio_chunk",
                                        "chunk": list(audio_chunk),
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

                except WebSocketDisconnect:
                    print("🔌 WebSocket disconnected during text processing")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON received: {e}")
                    continue
                except Exception as e:
                    print(f"❌ Error processing text input: {e}")
                    continue

        except WebSocketDisconnect:
            print("🔌 WebSocket disconnected")
        except Exception as e:
            print(f"❌ Error in WebSocket text input processing: {e}")
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
