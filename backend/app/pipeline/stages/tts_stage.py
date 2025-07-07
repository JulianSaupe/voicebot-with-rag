import asyncio
from typing import AsyncGenerator, Iterable

import numpy as np
from google.cloud import texttospeech

from backend.app.pipeline.pipeline_calls import TTSStageCall
from backend.app.pipeline.stages.stage import Stage

# Voices:
# - de-DE-Chirp3-HD-Aoede
# - de-DE-Chirp3-HD-Charon
# - de-DE-Chirp3-HD-Leda
# - de-DE-Chirp3-HD-Zephyr
# - de-DE-Chirp3-HD-Fenrir

class TTSStage(Stage):
    def __init__(self, language_code="de-DE"):
        self.client = texttospeech.TextToSpeechClient()
        self.language_code = language_code

    def __call__(self, data: TTSStageCall) -> AsyncGenerator[np.ndarray, None]:
        """Convert text stream to audio stream."""
        return self._convert_text_stream_to_audio(data.text_stream, data.voice)

    async def _convert_text_stream_to_audio(self, text_stream: Iterable[str], voice_name: str) -> AsyncGenerator[np.ndarray, None]:
        """Convert streaming text to streaming audio."""
        # Create streaming config with the specified voice
        streaming_config = texttospeech.StreamingSynthesizeConfig(
            voice=texttospeech.VoiceSelectionParams(
                name=voice_name,
                language_code=self.language_code,
            )
        )

        # Create an async queue to bridge sync text stream and async audio generation
        text_queue = asyncio.Queue()

        # Background task to consume the synchronous text stream
        async def text_producer():
            try:
                for chunk in text_stream:
                    await text_queue.put(chunk)
                    # Small delay to allow other tasks to run
                    await asyncio.sleep(0.001)
                await text_queue.put(None)  # Signal end
                print("📝 Text stream consumption complete")
            except Exception as exception:
                print(f"Error in text producer: {exception}")
                await text_queue.put(None)

        # Start the text producer task
        producer_task = asyncio.create_task(text_producer())

        sentence_buffer = ""
        full_answer = ""  # Store the complete answer

        print("🔊 Starting TTS conversion...")
        print("🤖 AI Answer:")
        print("-" * 50)

        try:
            while True:
                # Get text chunks from the queue
                text_chunk = await text_queue.get()
                if text_chunk is None:
                    break

                try:
                    if text_chunk:
                        # Print the text chunk to console immediately
                        print(text_chunk, end='', flush=True)
                        full_answer += text_chunk

                        sentence_buffer += text_chunk

                        # Check if we should synthesize
                        should_synthesize = (
                                self._is_sentence_complete(sentence_buffer) or
                                self._has_natural_break(sentence_buffer) or
                                self._should_break_at_word_boundary(sentence_buffer)
                        )

                        if should_synthesize and sentence_buffer.strip():
                            # Find the best break point to avoid splitting words
                            text_to_synthesize = self._get_text_to_synthesize(sentence_buffer)

                            if text_to_synthesize:
                                try:
                                    async for audio_chunk in self._synthesize_text(text_to_synthesize, streaming_config):
                                        yield audio_chunk
                                    # Remove the synthesized text from buffer
                                    sentence_buffer = sentence_buffer[len(text_to_synthesize):].lstrip()
                                except Exception as e:
                                    print(f"\n❌ Error synthesizing text chunk: {e}")
                                    sentence_buffer = ""

                except Exception as e:
                    print(f"\n❌ Error processing text chunk '{text_chunk}': {e}")
                    continue

            # Synthesize any remaining text
            if sentence_buffer.strip():
                try:
                    async for audio_chunk in self._synthesize_text(sentence_buffer.strip(), streaming_config):
                        yield audio_chunk
                except Exception as e:
                    print(f"\n❌ Error synthesizing final text: {e}")

        except Exception as e:
            print(f"\n❌ Fatal error in TTS conversion: {e}")
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

        print("\n" + "-" * 50)
        print(f"📝 Complete answer ({len(full_answer)} characters):")
        print(full_answer)
        print("-" * 50)
        print("🔊 TTS conversion complete")

    @staticmethod
    def _is_sentence_complete(text):
        """Check if text contains a complete sentence."""
        return any(punct in text for punct in ['.', '!', '?', '\n'])

    @staticmethod
    def _has_natural_break(text):
        """Check if text has a natural break point."""
        return any(punct in text for punct in [',', ';', ':', ' - ', ' – '])

    @staticmethod
    def _should_break_at_word_boundary(text):
        """Check if we should break at a word boundary due to length."""
        return len(text) > 80  # Increased threshold for better word boundaries

    @staticmethod
    def _get_text_to_synthesize(text):
        """Get the text to synthesize, ensuring we don't split words."""
        text = text.strip()
        if not text:
            return ""

        # If we have a sentence ending, use everything up to and including it
        sentence_endings = ['.', '!', '?', '\n']
        for ending in sentence_endings:
            if ending in text:
                pos = text.rfind(ending)
                if pos > 0:
                    return text[:pos + 2]

        # If we have natural breaks, use up to the last one
        natural_breaks = [',', ';', ':', ' - ', ' – ']
        for break_char in natural_breaks:
            if break_char in text:
                pos = text.rfind(break_char)
                if pos > 0:
                    return text[:pos + 2]

        # If text is long enough, find the last word boundary
        if len(text) > 80:
            # Find the last space before position 80
            words = text.split()
            if len(words) > 1:
                # Take all but the last word if we have multiple words
                return ' '.join(words[:-1]) + ' '

        # If text is short or we can't find a good break point, 
        # only return if we have a complete word
        if text.endswith(' ') or len(text) < 20:
            return text

        # Don't synthesize if we might be in the middle of a word
        return ""

    async def _synthesize_text(self, text: str, streaming_config) -> AsyncGenerator[np.ndarray, None]:
        """Synthesize a single text chunk to audio."""
        try:
            config_request = texttospeech.StreamingSynthesizeRequest(
                streaming_config=streaming_config
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
            print(f"\n❌ Synthesis error for text '{text[:50]}...': {e}")
            import traceback
            traceback.print_exc()
