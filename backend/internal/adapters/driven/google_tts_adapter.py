from typing import AsyncGenerator, Any

import numpy as np
from google.cloud import texttospeech

from backend.internal.ports.output.tts_port import TTSPort


class GoogleTTSAdapter(TTSPort):
    """Adapter for Google Cloud Text-to-Speech service."""

    def __init__(self, language_code: str = "de-DE"):
        self.client = texttospeech.TextToSpeechClient()
        self.language_code = language_code

    async def synthesize_speech(self, text: str, voice: str) -> bytes:
        """Synthesize speech from text using Google Cloud TTS."""
        try:
            # Configure the synthesis request
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice_params = texttospeech.VoiceSelectionParams(
                name=voice,
                language_code=self.language_code
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=24000
            )

            # Perform the text-to-speech request
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )

            return response.audio_content

        except Exception as e:
            print(f"❌ Error in Google TTS synthesis: {e}")
            raise RuntimeError(f"TTS synthesis failed: {str(e)}")

    async def synthesize_speech_stream(self, text_stream: AsyncGenerator[str, None],
                                       voice: str) -> AsyncGenerator[tuple[Any, str] | tuple[Any, str], None]:
        """Synthesize speech from streaming text using Google Cloud TTS."""
        try:
            # Create streaming config with the specified voice
            # Note: StreamingSynthesizeConfig doesn't support audio_config parameter
            # Audio format is determined by the streaming synthesis service defaults
            streaming_config = texttospeech.StreamingSynthesizeConfig(
                voice=texttospeech.VoiceSelectionParams(
                    name=voice,
                    language_code=self.language_code,
                )
            )

            sentence_buffer = ""

            async for text_chunk in text_stream:
                if text_chunk:
                    # Check if this chunk contains only punctuation
                    is_punctuation_only = self._is_punctuation_only_chunk(text_chunk)

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
                                    # Convert numpy array to list of integers for JSON serialization
                                    yield audio_chunk.astype(np.int16).tolist(), text_to_synthesize

                                # Remove the synthesized text from buffer
                                sentence_buffer = sentence_buffer[len(text_to_synthesize):].lstrip()

                                # If the current chunk was punctuation-only, we need to continue synthesis
                                # with the punctuation chunk but without the punctuation to avoid duplication
                                if is_punctuation_only and self._is_sentence_end_punctuation(text_chunk.strip()):
                                    # Create a continuation synthesis with the punctuation removed
                                    # This satisfies the requirement: "continue with the second chunk without the '.' etc."
                                    chunk_without_punctuation = self._remove_punctuation(text_chunk).strip()
                                    if chunk_without_punctuation:
                                        # If there's content after removing punctuation, synthesize it
                                        try:
                                            async for audio_chunk in self._synthesize_text(
                                                    chunk_without_punctuation, streaming_config):
                                                yield audio_chunk.astype(
                                                    np.int16).tolist(), chunk_without_punctuation
                                        except Exception as e:
                                            print(f"❌ Error synthesizing punctuation continuation: {e}")
                                    else:
                                        # If the chunk was only punctuation, create a minimal continuation
                                        # to satisfy the requirement of continuing synthesis
                                        try:
                                            # Use a very short pause or silence to continue the stream
                                            async for audio_chunk in self._synthesize_text(" ", streaming_config):
                                                yield audio_chunk.astype(np.int16).tolist(), " "
                                        except Exception as e:
                                            print(f"❌ Error synthesizing punctuation continuation: {e}")

                            except Exception as e:
                                print(f"❌ Error synthesizing text chunk: {e}")
                                sentence_buffer = ""

            # Synthesize any remaining text
            if sentence_buffer.strip():
                try:
                    async for audio_chunk in self._synthesize_text(sentence_buffer.strip(), streaming_config):
                        yield audio_chunk.astype(np.int16).tolist(), sentence_buffer.strip()
                except Exception as e:
                    print(f"❌ Error synthesizing final text: {e}")

        except Exception as e:
            print(f"❌ Error in Google TTS streaming synthesis: {e}")
            raise RuntimeError(f"TTS streaming synthesis failed: {str(e)}")

    @staticmethod
    def _is_sentence_complete(text: str) -> bool:
        """Check if the text contains a complete sentence."""
        return any(punct in text for punct in ['.', '!', '?'])

    @staticmethod
    def _has_natural_break(text: str) -> bool:
        """Check if the text has a natural break point."""
        return any(punct in text for punct in [',', ';', ':'])

    @staticmethod
    def _should_break_at_word_boundary(text: str) -> bool:
        """Check if we should break at a word boundary (for long text)."""
        return len(text) > 100 and text.endswith(' ')

    @staticmethod
    def _is_punctuation_only_chunk(text: str) -> bool:
        """Check if the text chunk contains only punctuation and whitespace."""
        stripped = text.strip()
        if not stripped:
            return False
        # Check if all characters are punctuation
        return all(c in '.!?,:;' for c in stripped)

    @staticmethod
    def _is_sentence_end_punctuation(text: str) -> bool:
        """Check if the text contains sentence-ending punctuation."""
        return any(punct in text for punct in ['.', '!', '?'])

    @staticmethod
    def _remove_punctuation(text: str) -> str:
        """Remove punctuation from text."""
        result = text
        for punct in '.!?,:;':
            result = result.replace(punct, '')
        return result

    @staticmethod
    def _get_text_to_synthesize(text: str) -> str:
        """Get the portion of text that should be synthesized."""
        # Find the last complete sentence or natural break
        for punct in ['.', '!', '?']:
            if punct in text:
                idx = text.rfind(punct)
                return text[:idx + 1].strip()

        # If no sentence end, look for natural breaks
        for punct in [',', ';', ':']:
            if punct in text:
                idx = text.rfind(punct)
                return text[:idx + 1].strip()

        # If text is long enough, break at word boundary
        if len(text) > 100:
            words = text.split()
            if len(words) > 1:
                return ' '.join(words[:-1]) + ' '

        return text.strip()

    async def _synthesize_text(self, text: str, streaming_config) -> AsyncGenerator[np.ndarray, None]:
        """Synthesize a single text chunk using streaming TTS."""

        def request_generator():
            yield texttospeech.StreamingSynthesizeRequest(streaming_config=streaming_config)
            yield texttospeech.StreamingSynthesizeRequest(input=texttospeech.StreamingSynthesisInput(text=text))

        try:
            response_stream = self.client.streaming_synthesize(request_generator())

            for response in response_stream:
                if response.audio_content:
                    # Convert audio bytes to numpy array
                    audio_data = np.frombuffer(response.audio_content, dtype=np.int16)
                    yield audio_data

        except Exception as e:
            print(f"❌ Error in streaming synthesis: {e}")
            raise
