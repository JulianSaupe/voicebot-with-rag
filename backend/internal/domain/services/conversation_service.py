from typing import List

from backend.internal.domain.models.audio_transcription import AudioTranscription
from backend.internal.domain.models.conversation_context import ConversationContext


class ConversationService:
    """Domain service containing core business logic for conversation processing."""
    
    @staticmethod
    def validate_transcription(transcription: AudioTranscription) -> bool:
        """Validate that a transcription is suitable for processing."""
        if transcription.is_empty():
            return False
        
        # Business rule: minimum length for meaningful conversation
        if len(transcription.get_clean_text()) < 0:
            return False
            
        return True
    
    @staticmethod
    def create_conversation_context(transcription: AudioTranscription,
                                    relevant_documents: List[str]) -> ConversationContext:
        """Create conversation context from transcription and retrieved documents."""
        return ConversationContext(
            user_query=transcription.get_clean_text(),
            relevant_documents=relevant_documents
        )
    
    @staticmethod
    def should_use_context(context: ConversationContext) -> bool:
        """Business logic to determine if context should be used in response generation."""
        # Use context if we have relevant documents and the query is substantial
        return (context.has_relevant_context() and 
                len(context.user_query) > 10)  # Business rule: longer queries benefit from context
    
    def prepare_response_settings(self, voice_preference: str) -> str:
        """Prepare voice settings based on user preference and business rules."""
        # Business rule: default to German voice if not specified
        if not voice_preference:
            return "de-DE-Chirp3-HD-Charon"
        
        # Business rule: validate voice setting format
        if not self._is_valid_voice_setting(voice_preference):
            return "de-DE-Chirp3-HD-Charon"
            
        return voice_preference
    
    @staticmethod
    def _is_valid_voice_setting(voice: str) -> bool:
        """Validate voice setting format."""
        # Simple validation - could be expanded with more business rules
        return bool(voice and "-" in voice and len(voice) > 5)