import time
from fastapi import WebSocket, WebSocketDisconnect
import json
import numpy as np
from backend.internal.application.voicebot_service import VoicebotService
from backend.internal.application.voice_activity_detector_service import VoiceActivityDetector
from backend.internal.domain.models.audio_transcription import AudioTranscription


class VoicebotController:
    """Web controller for voicebot endpoints using hexagonal architecture."""

    # Constants
    DEFAULT_LANGUAGE_CODE: str = "de-DE"
    DEFAULT_VOICE: str = "de-DE-Chirp3-HD-Charon"
    VAD_SILENCE_THRESHOLD_MS: int = 200
    VAD_MIN_SPEECH_DURATION_MS: int = 100
    VAD_SAMPLE_RATE: int = 48000
    MIN_TRANSCRIPTION_LENGTH: int = 1

    def __init__(self, voicebot_service: VoicebotService):
        self.voicebot_service = voicebot_service

    def _create_vad_detector(self) -> VoiceActivityDetector:
        """Create VAD detector with optimized parameters."""
        return VoiceActivityDetector(
            silence_threshold_ms=self.VAD_SILENCE_THRESHOLD_MS,
            min_speech_duration_ms=self.VAD_MIN_SPEECH_DURATION_MS,
            sample_rate=self.VAD_SAMPLE_RATE
        )

    @staticmethod
    def _create_transcription_message(transcription: AudioTranscription) -> dict:
        """Create transcription message template."""
        return {
            "type": "transcription",
            "transcription": transcription.text,
            "confidence": transcription.confidence,
            "language_code": transcription.language_code,
            "status": "success"
        }

    @staticmethod
    def _create_audio_message(audio_chunk, chunk_number: int, response_id: int, llm_response: str = None) -> dict:
        """Create audio message template."""
        msg = {
            "type": "audio",
            "data": list(audio_chunk),
            "chunk_number": chunk_number,
            "status": "streaming",
            "id": response_id,
        }
        if llm_response:
            msg["llm_response"] = llm_response
        return msg

    @staticmethod
    def _create_error_message(error_type: str, error_message: str) -> dict:
        """Create error message template."""
        return {
            "type": error_type,
            "error": error_message,
            "status": "error"
        }

    @staticmethod
    def _create_end_message(total_chunks: int) -> dict:
        """Create end of stream message template."""
        return {
            "type": "audio_end",
            "total_chunks": total_chunks,
            "status": "complete"
        }

    @staticmethod
    async def _send_json_message(websocket: WebSocket, message: dict):
        """Send JSON message via WebSocket with error handling."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            pass  # Connection might be closed

    async def _process_transcription_and_generate_audio(self, websocket: WebSocket, transcription: AudioTranscription,
                                                        start_time: float):
        """Process transcription through LLM and stream audio response."""
        try:
            print(f"🤖 Processing transcription through LLM: {transcription.text}")

            audio_stream = self.voicebot_service.generate_streaming_voice_response(
                transcription.text, voice=self.DEFAULT_VOICE
            )

            await self._stream_audio_response(websocket, audio_stream)

            total_time = time.time() - start_time
            print(f"⚡ Total processing time: {total_time:.3f}s")

        except Exception as llm_error:
            print(f"❌ Error in LLM processing or audio generation: {llm_error}")
            import traceback
            traceback.print_exc()

            error_message = self._create_error_message(
                "audio_error", f"Failed to generate audio response: {str(llm_error)}"
            )
            await self._send_json_message(websocket, error_message)

    async def _stream_audio_response(self, websocket: WebSocket, audio_stream, response_id: int = None):
        """Stream audio chunks back via WebSocket."""
        chunk_count = 0
        previous_text = None
        if response_id is None:
            response_id = int(time.time())

        async for audio_chunk, text in audio_stream:
            if audio_chunk:
                chunk_count += 1
                llm_response = text if text != previous_text else None
                audio_message = self._create_audio_message(audio_chunk, chunk_count, response_id, llm_response)
                previous_text = text
                await self._send_json_message(websocket, audio_message)

        end_message = self._create_end_message(chunk_count)
        await self._send_json_message(websocket, end_message)
        print(f"🔊 Audio streaming complete - sent {chunk_count} chunks")

    async def _handle_transcription(self, websocket: WebSocket, audio_data: np.ndarray, start_time: float):
        """Handle transcription of audio data."""
        try:
            transcription = await self.voicebot_service.transcribe_audio(
                audio_data, language_code=self.DEFAULT_LANGUAGE_CODE
            )

            if transcription.text and len(transcription.text.strip()) > self.MIN_TRANSCRIPTION_LENGTH:
                transcription_result = self._create_transcription_message(transcription)
                print(f"🎤 VAD-based transcription: {transcription.text}")
                await self._send_json_message(websocket, transcription_result)
                await self._process_transcription_and_generate_audio(websocket, transcription, start_time)

        except Exception as e:
            print(f"❌ Transcription error: {e}")
            error_result = self._create_error_message("error", f"Transcription failed: {str(e)}")
            await self._send_json_message(websocket, error_result)

    async def _process_final_audio(self, websocket: WebSocket, vad: VoiceActivityDetector):
        """Process any remaining buffered audio when connection closes."""
        final_audio = vad.force_process_buffer()
        if not final_audio:
            return

        print("🎤 Processing final buffered audio")
        try:
            final_transcription = await self.voicebot_service.transcribe_audio(
                final_audio, language_code=self.DEFAULT_LANGUAGE_CODE
            )

            if final_transcription.text and len(final_transcription.text.strip()) > self.MIN_TRANSCRIPTION_LENGTH:
                transcription_result = self._create_transcription_message(final_transcription)
                await self._send_json_message(websocket, transcription_result)

                try:
                    print(f"🤖 Processing final transcription through LLM: {final_transcription.text}")
                    audio_stream = self.voicebot_service.generate_streaming_voice_response(
                        final_transcription.text, voice=self.DEFAULT_VOICE
                    )
                    await self._stream_audio_response(websocket, audio_stream)

                except Exception as llm_error:
                    print(f"❌ Error in final LLM processing or audio generation: {llm_error}")
                    error_message = self._create_error_message(
                        "audio_error", f"Failed to generate final audio response: {str(llm_error)}"
                    )
                    await self._send_json_message(websocket, error_message)

        except Exception as e:
            print(f"❌ Failed to transcribe final audio: {e}")

    async def transcribe_audio_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection for real-time audio transcription with VAD."""
        await websocket.accept()
        print("🔌 WebSocket connection established for VAD-based audio transcription")

        vad = self._create_vad_detector()

        try:
            while True:
                try:
                    message = await websocket.receive_text()
                    data = json.loads(message)

                    if data['type'] == 'pcm':
                        pcm_data = np.array(data['data'], dtype=np.float32)
                        start_time = time.time()

                        should_transcribe, accumulated_audio = vad.process_audio_chunk(pcm_data)

                        if should_transcribe and accumulated_audio is not None and len(accumulated_audio) > 0:
                            await self._handle_transcription(websocket, accumulated_audio, start_time)

                except WebSocketDisconnect:
                    print("🔌 WebSocket disconnected during audio streaming")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON received: {e}")
                    continue
                except Exception as e:
                    print(f"❌ Error processing audio chunk: {e}")
                    continue

            await self._process_final_audio(websocket, vad)

        except WebSocketDisconnect:
            print("🔌 WebSocket disconnected")
        except Exception as e:
            print(f"❌ Error in WebSocket audio transcription: {e}")
            import traceback
            traceback.print_exc()

            error_result = self._create_error_message("error", str(e))
            await self._send_json_message(websocket, error_result)

    async def text_input_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection for text input with audio response streaming."""
        await websocket.accept()
        print("🔌 WebSocket connection established for text input with audio response")

        try:
            while True:
                try:
                    message = await websocket.receive_text()
                    data = json.loads(message)

                    if data['type'] == 'text_prompt':
                        await self._handle_text_input(websocket, data['data'])

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

            error_result = self._create_error_message("error", str(e))
            await self._send_json_message(websocket, error_result)

    async def _handle_text_input(self, websocket: WebSocket, data: dict):
        """Handle text input and generate audio response."""
        text_input = data.get('text', '').strip()
        voice = data.get('voice', self.DEFAULT_VOICE)

        if not text_input:
            error_message = self._create_error_message("audio_error", "Empty text input received")
            await self._send_json_message(websocket, error_message)
            return

        print(f"🤖 Processing text input through LLM: {text_input}")
        start_time = time.time()

        try:
            audio_stream = self.voicebot_service.generate_streaming_voice_response(text_input, voice=voice)

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
                    await self._send_json_message(websocket, audio_message)

            end_message = self._create_end_message(chunk_count)
            await self._send_json_message(websocket, end_message)
            print(f"🔊 Audio streaming complete - sent {chunk_count} chunks")

            total_time = time.time() - start_time
            print(f"⚡ Total processing time: {total_time:.3f}s")

        except Exception as llm_error:
            print(f"❌ Error in LLM processing or audio generation: {llm_error}")
            import traceback
            traceback.print_exc()

            error_message = self._create_error_message(
                "audio_error", f"Failed to generate audio response: {str(llm_error)}"
            )
            await self._send_json_message(websocket, error_message)
