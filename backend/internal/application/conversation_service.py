from typing import List

from backend.internal.domain.models.audio_transcription import AudioTranscription
from backend.internal.domain.models.conversation_context import ConversationContext


class ConversationService:
    """Domain service containing core business logic for conversation processing."""

    def __init__(self):
        self.history = []

    @staticmethod
    def validate_transcription(transcription: AudioTranscription) -> bool:
        """Validate that a transcription is suitable for processing."""
        if transcription.is_empty():
            return False

        if len(transcription.get_clean_text()) < 0:
            return False

        return True

    def add_to_history(self, text: str) -> None:
        """Add conversation context to history."""
        self.history.append(text)

    def create_conversation_context(self, transcription: AudioTranscription,
                                    relevant_documents: List[str]) -> ConversationContext:
        """Create conversation context from transcription and retrieved documents."""
        return ConversationContext(
            user_query=transcription.get_clean_text(),
            relevant_documents=relevant_documents,
            conversation_history=self.history[-10:]
        )

    @staticmethod
    def prepare_response_settings(voice_preference: str) -> str:
        """Prepare voice settings based on user preference and business rules."""
        if not voice_preference:
            return "de-DE-Chirp3-HD-Charon"

        return voice_preference
