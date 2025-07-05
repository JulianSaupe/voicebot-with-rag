import asyncio
import numpy as np
from typing import AsyncGenerator, Iterable
from google.cloud import texttospeech

from app.pipeline.pipeline_calls import TTSStageCall
from app.pipeline.stages.stage import Stage


class TTSStage(Stage):
    def __init__(self, voice_name="de-DE-Chirp3-HD-Charon", language_code="de-DE"):
        self.client = texttospeech.TextToSpeechClient()
        self.streaming_config = texttospeech.StreamingSynthesizeConfig(
            voice=texttospeech.VoiceSelectionParams(
                name=voice_name,
                language_code=language_code,
            )
        )

    def __call__(self, data: TTSStageCall) -> AsyncGenerator[np.ndarray, None]:
        """Convert text stream to audio stream."""
        return self._convert_text_stream_to_audio(data.text_stream)

    async def _convert_text_stream_to_audio(self, text_stream: Iterable[str]) -> AsyncGenerator[np.ndarray, None]:
        """Convert streaming text to streaming audio."""
        # Create an async queue to bridge sync text stream and async audio generation
        text_queue = asyncio.Queue()
        
        # Background task to consume the synchronous text stream
        async def text_producer():
            try:
                for text_chunk in text_stream:
                    await text_queue.put(text_chunk)
                    # Small delay to allow other tasks to run
                    await asyncio.sleep(0.001)
                await text_queue.put(None)  # Signal end
                print("📝 Text stream consumption complete")
            except Exception as e:
                print(f"Error in text producer: {e}")
                await text_queue.put(None)
        
        # Start the text producer task
        producer_task = asyncio.create_task(text_producer())
        
        sentence_buffer = ""
        print("🔊 Starting TTS conversion...")
        
        try:
            while True:
                # Get text chunks from the queue
                text_chunk = await text_queue.get()
                if text_chunk is None:
                    break
                
                try:
                    if text_chunk:
                        print(f"📝 Processing text: '{text_chunk}'")
                        sentence_buffer += text_chunk
                        
                        # More aggressive streaming - synthesize smaller chunks
                        should_synthesize = (
                            self._is_sentence_complete(sentence_buffer) or 
                            len(sentence_buffer) > 30 or
                            self._has_natural_break(sentence_buffer)
                        )
                        
                        if should_synthesize and sentence_buffer.strip():
                            print(f"🎵 Synthesizing: '{sentence_buffer.strip()}'")
                            try:
                                async for audio_chunk in self._synthesize_text(sentence_buffer.strip()):
                                    yield audio_chunk
                                sentence_buffer = ""
                            except Exception as e:
                                print(f"Error synthesizing text chunk: {e}")
                                sentence_buffer = ""
                                    
                except Exception as e:
                    print(f"Error processing text chunk '{text_chunk}': {e}")
                    continue
            
            # Synthesize any remaining text
            if sentence_buffer.strip():
                print(f"🎵 Synthesizing final: '{sentence_buffer.strip()}'")
                try:
                    async for audio_chunk in self._synthesize_text(sentence_buffer.strip()):
                        yield audio_chunk
                except Exception as e:
                    print(f"Error synthesizing final text: {e}")
                    
        except Exception as e:
            print(f"Fatal error in TTS conversion: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Ensure the producer task is cleaned up
            if not producer_task.done():
                producer_task.cancel()
                try:
                    await producer_task
                except asyncio.CancelledError:
                    pass
        
        print("🔊 TTS conversion complete")

    def _is_sentence_complete(self, text):
        """Check if text contains a complete sentence."""
        return any(punct in text for punct in ['.', '!', '?', '\n'])
    
    def _has_natural_break(self, text):
        """Check if text has a natural break point."""
        return any(punct in text for punct in [',', ';', ':', ' - ', ' – '])

    async def _synthesize_text(self, text: str) -> AsyncGenerator[np.ndarray, None]:
        """Synthesize a single text chunk to audio."""
        try:
            config_request = texttospeech.StreamingSynthesizeRequest(
                streaming_config=self.streaming_config
            )
            
            text_request = texttospeech.StreamingSynthesizeRequest(
                input=texttospeech.StreamingSynthesisInput(text=text)
            )
            
            def request_generator():
                yield config_request
                yield text_request
            
            streaming_responses = self.client.streaming_synthesize(request_generator())
            
            for response in streaming_responses:
                if len(response.audio_content) > 0:
                    audio_data = np.frombuffer(response.audio_content, dtype=np.int16)
                    yield audio_data
                    
        except Exception as e:
            print(f"Synthesis error for text '{text[:50]}...': {e}")
            import traceback
            traceback.print_exc()