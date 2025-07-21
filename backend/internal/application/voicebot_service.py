from typing import AsyncGenerator, Any
import numpy as np

from backend.internal.ports.output.llm_port import LLMPort
from backend.internal.ports.output.rag_port import RAGPort
from backend.internal.ports.output.speech_recognition_port import SpeechRecognitionPort
from backend.internal.ports.output.tts_port import TTSPort
from backend.internal.domain.models.audio_transcription import AudioTranscription
from backend.internal.domain.models.voice_response import VoiceResponse
from backend.internal.domain.services.conversation_service import ConversationService


class VoicebotService:
    """Application service orchestrating the complete voicebot conversation flow."""

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

    async def transcribe_audio(self, audio_data: np.ndarray, language_code: str = "de-DE") -> AudioTranscription:
        """Transcribe audio data to text using the speech recognition port."""
        transcription = await self.speech_recognition.transcribe_audio(audio_data, language_code)

        if not self.conversation_service.validate_transcription(transcription):
            raise ValueError("Invalid transcription: empty or too short")

        return transcription

    async def generate_voice_response(self, prompt: str, voice: str = None) -> VoiceResponse:
        """Generate a complete voice response from a text prompt."""
        # Prepare voice settings using domain logic
        voice_settings = self.conversation_service.prepare_response_settings(voice)

        # Retrieve relevant context
        relevant_documents = await self.rag.retrieve_relevant_documents(prompt)

        # Create conversation context using domain service
        context = self.conversation_service.create_conversation_context(
            AudioTranscription(text=prompt),
            relevant_documents
        )

        # Build prompt with context if appropriate
        final_prompt = self._build_prompt_with_context(context)

        # Generate text response
        text_response = await self.llm.generate_response(final_prompt)

        return VoiceResponse(
            text_content=text_response,
            voice_settings=voice_settings
        )

    async def generate_streaming_voice_response(self, prompt: str, voice: str = None) -> AsyncGenerator[
        tuple[Any, Any], None]:
        """Generate a streaming voice response from a text prompt."""
        # Prepare voice settings using domain logic
        voice_settings = self.conversation_service.prepare_response_settings(voice)

        # Retrieve relevant context
        relevant_documents = await self.rag.retrieve_relevant_documents(prompt)

        # Create conversation context using domain service
        context = self.conversation_service.create_conversation_context(
            AudioTranscription(text=prompt),
            relevant_documents
        )

        # Build prompt with context if appropriate
        final_prompt = self._build_prompt_with_context(context)

        # Generate streaming text response
        text_stream = self.llm.generate_response_stream(final_prompt)

        # Convert text stream to audio stream
        async for audio_chunk, text in self.tts.synthesize_speech_stream(text_stream, voice_settings):
            yield audio_chunk, text

    def _build_prompt_with_context(self, context) -> str:
        """Build the final prompt including context if appropriate."""
        base_prompt = (
            "Du bist ein KI Agent, welcher Antworten auf Fragen von den Nutzer geben kann. "
            "Rege den Nutzer am Ende deiner Antwort an weitere Fragen zu stellen und mache dazu einige Vorschläge. "
            "Gebe nur ganze Sätze wieder, welche mit Hilfe von TTS an den Benutzer ausgegeben werden."
        )

        if self.conversation_service.should_use_context(context):
            return f"{base_prompt}\n\nKontext:\n{context.get_context_summary()}\n\nFrage: {context.user_query}"
        else:
            return f"{base_prompt}\n\nFrage: {context.user_query}"
