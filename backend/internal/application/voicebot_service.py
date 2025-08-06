from typing import AsyncGenerator, Any
import numpy as np
from functools import lru_cache
import hashlib

from backend.internal.ports.output.llm_port import LLMPort
from backend.internal.ports.output.rag_port import RAGPort
from backend.internal.ports.output.speech_recognition_port import SpeechRecognitionPort
from backend.internal.ports.output.tts_port import TTSPort
from backend.internal.domain.models.audio_transcription import AudioTranscription
from backend.internal.domain.models.voice_response import VoiceResponse
from backend.internal.application.conversation_service import ConversationService


class VoicebotService:
    """Application service orchestrating the complete voicebot conversation flow."""

    # Simple in-memory cache for LLM responses
    _llm_cache = {}
    _cache_max_size = 32

    def __init__(self,
                 speech_recognition: SpeechRecognitionPort,
                 rag: RAGPort,
                 llm: LLMPort,
                 tts: TTSPort,
                 conversation_service: ConversationService):
        self.speech_recognition = speech_recognition
        self.rag = rag
        self.llm = llm
        self.tts = tts
        self.conversation_service = conversation_service

    def _get_prompt_hash(self, prompt: str) -> str:
        """Generate hash for prompt caching"""
        return hashlib.md5(prompt.encode()).hexdigest()

    async def _get_cached_llm_response(self, final_prompt: str) -> str:
        """Get cached LLM response or generate new one"""
        prompt_hash = self._get_prompt_hash(final_prompt)

        # Check cache first
        if prompt_hash in self._llm_cache:
            print(f"🧊 Using cached LLM response for prompt hash: {prompt_hash[:8]}...")
            return self._llm_cache[prompt_hash]

        # Generate new response
        text_response = await self.llm.generate_response(final_prompt)

        # Cache the response (with simple size limit)
        if len(self._llm_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._llm_cache))
            del self._llm_cache[oldest_key]

        self._llm_cache[prompt_hash] = text_response
        print(f"🧊 Cached new LLM response for prompt hash: {prompt_hash[:8]}...")
        return text_response

    async def transcribe_audio(self, audio_data: np.ndarray, language_code: str = "de-DE") -> AudioTranscription:
        """Transcribe audio data to text using the speech recognition port."""
        # Profiler removed for performance - direct transcription
        transcription = await self.speech_recognition.transcribe_audio(audio_data, language_code)

        if not self.conversation_service.validate_transcription(transcription):
            raise ValueError("Invalid transcription: empty or too short")

        return transcription

    async def generate_voice_response(self, prompt: str, voice: str = None) -> VoiceResponse:
        """Generate a complete voice response from a text prompt."""
        # Prepare voice settings using domain logic
        voice_settings = self.conversation_service.prepare_response_settings(voice)

        # Retrieve relevant context (profiler removed for performance)
        relevant_documents = await self.rag.retrieve_relevant_documents(prompt)

        # Create conversation context using domain service
        context = self.conversation_service.create_conversation_context(
            AudioTranscription(text=prompt),
            relevant_documents
        )

        # Build prompt with context if appropriate
        final_prompt = self._build_prompt_with_context(context)

        # Generate text response with caching (profiler removed for performance)
        text_response = await self._get_cached_llm_response(final_prompt)

        return VoiceResponse(
            text_content=text_response,
            voice_settings=voice_settings
        )

    async def generate_streaming_voice_response(self, prompt: str, voice: str = None) -> AsyncGenerator[
        tuple[Any, Any], None]:
        """Generate a streaming voice response from a text prompt."""
        # Prepare voice settings using domain logic
        voice_settings = self.conversation_service.prepare_response_settings(voice)

        # Retrieve relevant context (profiler removed for performance)
        relevant_documents = await self.rag.retrieve_relevant_documents(prompt)

        # Create conversation context using domain service
        context = self.conversation_service.create_conversation_context(
            AudioTranscription(text=prompt),
            relevant_documents
        )

        # Build prompt with context if appropriate
        final_prompt = self._build_prompt_with_context(context)

        # Generate streaming text response (profiler removed for performance)
        text_stream = self.llm.generate_response_stream(final_prompt)

        # Convert text stream to audio stream (profiler removed for performance)
        async for audio_chunk, text in self.tts.synthesize_speech_stream(text_stream, voice_settings):
            yield audio_chunk, text

    def _build_prompt_with_context(self, context) -> str:
        """Build the final prompt including context if appropriate."""
        base_prompt = (
            "Du bist ein KI Agent, welcher ausführliche Antworten auf Fragen von Nutzern geben kann."
            "Unter 'Frage' ist die Frage des nutzers gegeben."
            "Unter 'Kontext' ist weiterer Kontext bereitgestellt, welcher bei der Beantwortung der Frage hilfreich sein kann."
            "Nutze den Kontext, wenn möglich um die Frage zu beantworten."
            "Ist der Kontext nicht hilfreich, ignoriere ihn."
            # "Rege den Nutzer am Ende deiner Antwort an weitere Fragen zu stellen und mache dazu einige Vorschläge. "
            "Gebe nur ganze Sätze wieder, welche mit Hilfe von TTS an den Benutzer ausgegeben werden."
        )

        if self.conversation_service.should_use_context(context):
            return f"{base_prompt}\n\nKontext:\n{context.get_context_summary()}\n\nFrage: {context.user_query}"
        else:
            return f"{base_prompt}\n\nFrage: {context.user_query}"
