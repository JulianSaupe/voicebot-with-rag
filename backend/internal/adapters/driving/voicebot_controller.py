import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from backend.internal.application.voice_activity_detector_service import VoiceActivityDetector
from backend.internal.application.voicebot_service import VoicebotService
from backend.internal.domain.services.async_process_manager import AsyncProcessManager, AsyncCancellationToken


class VoicebotController:
    """Web controller for voicebot endpoints using hexagonal architecture."""

    def __init__(self, voicebot_service: VoicebotService, process_manager: AsyncProcessManager, container_instance=None):
        self.voicebot_service = voicebot_service
        self.process_manager = process_manager
        self.container = container_instance  # Store container reference for creating cancellable adapters
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.active_transcription_processes: Dict[str, str] = {}  # websocket_id -> process_id

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

                    if data['type'] == 'start_transcription':
                        # Handle start transcription request
                        await self._handle_start_transcription(websocket, data)
                    
                    elif data['type'] == 'stop_transcription':
                        # Handle stop transcription request
                        await self._handle_stop_transcription(websocket, data)
                    
                    elif data['type'] == 'stop_all_transcriptions':
                        # Handle stop all transcriptions request
                        await self._handle_stop_all_transcriptions(websocket, data)
                    
                    elif data['type'] == 'pcm':
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
                                        print(f"Text chunk: {text}")
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

    async def _handle_start_transcription(self, websocket: WebSocket, data: dict):
        """Handle start transcription request."""
        try:
            audio_data = data.get('audio_data')
            language_code = data.get('language_code', 'de-DE')
            metadata = data.get('metadata', {})
            
            if not audio_data:
                await websocket.send_text(json.dumps({
                    "type": "transcription_error",
                    "error": "No audio data provided",
                    "status": "error"
                }))
                return
            
            # Start a new process
            process_id, cancellation_token = self.process_manager.start_process(
                name="speech_transcription",
                metadata={
                    "language_code": language_code,
                    "websocket_id": id(websocket),
                    **metadata
                }
            )
            
            # Store the process ID for this WebSocket connection
            websocket_id = str(id(websocket))
            self.active_transcription_processes[websocket_id] = process_id
            
            # Emit transcription started event
            await websocket.send_text(json.dumps({
                "type": "transcription_started",
                "process_id": process_id,
                "status": "started"
            }))
            
            # Run the transcription process in a separate thread
            loop = asyncio.get_event_loop()
            loop.run_in_executor(
                self.executor,
                self._run_transcription_process,
                process_id,
                cancellation_token,
                audio_data,
                language_code,
                websocket
            )
            
        except Exception as e:
            print(f"❌ Error starting transcription: {e}")
            await websocket.send_text(json.dumps({
                "type": "transcription_error",
                "error": f"Failed to start transcription: {str(e)}",
                "status": "error"
            }))

    async def _handle_stop_transcription(self, websocket: WebSocket, data: dict):
        """Handle stop transcription request."""
        try:
            process_id = data.get('process_id')
            reason = data.get('reason', 'Stopped by user')
            
            if not process_id:
                # Try to get process ID from active processes
                websocket_id = str(id(websocket))
                process_id = self.active_transcription_processes.get(websocket_id)
            
            if not process_id:
                await websocket.send_text(json.dumps({
                    "type": "transcription_error",
                    "error": "No active transcription process found",
                    "status": "error"
                }))
                return
            
            # Stop the process
            success = await self.process_manager.stop_process(process_id, reason)
            
            if success:
                # Clean up the process tracking
                websocket_id = str(id(websocket))
                if websocket_id in self.active_transcription_processes:
                    del self.active_transcription_processes[websocket_id]
                
                await websocket.send_text(json.dumps({
                    "type": "transcription_stopped",
                    "process_id": process_id,
                    "reason": reason,
                    "status": "stopped"
                }))
            else:
                await websocket.send_text(json.dumps({
                    "type": "transcription_error",
                    "error": f"Process {process_id} not found or already stopped",
                    "status": "error"
                }))
                
        except Exception as e:
            print(f"❌ Error stopping transcription: {e}")
            await websocket.send_text(json.dumps({
                "type": "transcription_error",
                "error": f"Failed to stop transcription: {str(e)}",
                "status": "error"
            }))

    async def _handle_stop_all_transcriptions(self, websocket: WebSocket, data: dict):
        """Handle stop all transcriptions request."""
        try:
            reason = data.get('reason', 'All processes stopped by user')
            
            # Stop all processes
            stopped_count = await self.process_manager.stop_all_processes(reason)
            
            # Clear all active process tracking
            self.active_transcription_processes.clear()
            
            await websocket.send_text(json.dumps({
                "type": "all_transcriptions_stopped",
                "stopped_count": stopped_count,
                "reason": reason,
                "status": "stopped"
            }))
            
        except Exception as e:
            print(f"❌ Error stopping all transcriptions: {e}")
            await websocket.send_text(json.dumps({
                "type": "transcription_error",
                "error": f"Failed to stop all transcriptions: {str(e)}",
                "status": "error"
            }))

    def _run_transcription_process(self, process_id: str, cancellation_token: AsyncCancellationToken, 
                                 audio_data: list, language_code: str, websocket: WebSocket):
        """Run transcription process in a separate thread with proper event loop management."""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async transcription process
            loop.run_until_complete(
                self._async_transcription_process(
                    process_id, cancellation_token, audio_data, language_code, websocket
                )
            )
            
        except Exception as e:
            print(f"❌ Error in transcription process thread: {e}")
        finally:
            # Clean up the event loop
            try:
                loop.close()
            except:
                pass
            
            # Clean up the process
            self.process_manager.cleanup_process(process_id)

    async def _async_transcription_process(self, process_id: str, cancellation_token: AsyncCancellationToken,
                                         audio_data: list, language_code: str, websocket: WebSocket):
        """Main async transcription processing logic."""
        try:
            # Convert audio data to numpy array
            audio_array = np.array(audio_data, dtype=np.float32)
            
            # Create a cancellable speech adapter with the cancellation token
            speech_adapter = self.container.create_cancellable_speech_adapter_with_token(cancellation_token)
            
            # Emit progress update
            await self._emit_websocket_event(websocket, {
                "type": "transcription_progress",
                "process_id": process_id,
                "status": "processing",
                "message": "Starting transcription..."
            })
            
            # Perform transcription with cancellation support
            transcription = await speech_adapter.transcribe_audio(audio_array, language_code)
            
            # Check if cancelled during transcription
            if cancellation_token.is_cancelled():
                await self._emit_websocket_event(websocket, {
                    "type": "transcription_cancelled",
                    "process_id": process_id,
                    "reason": cancellation_token.cancellation_reason,
                    "status": "cancelled"
                })
                return
            
            # Emit successful completion
            await self._emit_websocket_event(websocket, {
                "type": "transcription_completed",
                "process_id": process_id,
                "transcription": transcription.text,
                "confidence": transcription.confidence,
                "language_code": transcription.language_code,
                "status": "completed"
            })
            
        except asyncio.CancelledError:
            # Handle cancellation
            await self._emit_websocket_event(websocket, {
                "type": "transcription_cancelled",
                "process_id": process_id,
                "reason": cancellation_token.cancellation_reason or "Process cancelled",
                "status": "cancelled"
            })
            
        except Exception as e:
            # Handle other errors
            print(f"❌ Error in async transcription process: {e}")
            await self._emit_websocket_event(websocket, {
                "type": "transcription_error",
                "process_id": process_id,
                "error": str(e),
                "status": "error"
            })

    async def _emit_websocket_event(self, websocket: WebSocket, event: dict):
        """Safely emit WebSocket event with error handling."""
        try:
            await websocket.send_text(json.dumps(event))
        except Exception as e:
            print(f"❌ Failed to emit WebSocket event: {e}")
            # Don't re-raise as this could break the process flow
