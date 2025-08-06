"""Dependency injection container for ports and adapters architecture."""

from backend.internal.adapters.driven.all_mpnet_base_v2 import AllMPNetBaseV2
from backend.internal.adapters.driven.postgres_db import PostgresVectorDB
from backend.internal.application.voicebot_service import VoicebotService
from backend.internal.application.conversation_service import ConversationService
from backend.internal.adapters.driven.gemini_llm_adapter import GeminiLLMAdapter
from backend.internal.adapters.driven.google_speech_adapter import GoogleSpeechAdapter
from backend.internal.adapters.driven.google_tts_adapter import GoogleTTSAdapter
from backend.internal.adapters.driven.rag_adapter import RAGAdapter
from backend.internal.adapters.driving.voicebot_controller import VoicebotController


class Container:
    """Dependency injection container for the voicebot application using ports and adapters pattern."""
    
    def __init__(self):
        self._instances = {}
    
    
    def get_conversation_service(self) -> ConversationService:
        """Get or create ConversationService instance."""
        if 'conversation_service' not in self._instances:
            self._instances['conversation_service'] = ConversationService()
        return self._instances['conversation_service']
    
    def get_speech_recognition_adapter(self) -> GoogleSpeechAdapter:
        """Get or create GoogleSpeechAdapter instance."""
        if 'speech_recognition_adapter' not in self._instances:
            self._instances['speech_recognition_adapter'] = GoogleSpeechAdapter()
        return self._instances['speech_recognition_adapter']
    
    def get_llm_adapter(self) -> GeminiLLMAdapter:
        """Get or create GeminiLLMAdapter instance."""
        if 'llm_adapter' not in self._instances:
            self._instances['llm_adapter'] = GeminiLLMAdapter()
        return self._instances['llm_adapter']
    
    def get_rag_adapter(self) -> RAGAdapter:
        """Get or create RAGAdapter instance."""
        if 'rag_adapter' not in self._instances:
            # Create embedding calculator and vector database
            embedding_calculator = AllMPNetBaseV2()
            vector_db = PostgresVectorDB(embedding_calculator)
            
            self._instances['rag_adapter'] = RAGAdapter(
                embedding_calculator, 
                vector_db
            )
        return self._instances['rag_adapter']
    
    def get_tts_adapter(self) -> GoogleTTSAdapter:
        """Get or create GoogleTTSAdapter instance."""
        if 'tts_adapter' not in self._instances:
            self._instances['tts_adapter'] = GoogleTTSAdapter()
        return self._instances['tts_adapter']
    
    def get_voicebot_service(self) -> VoicebotService:
        """Get or create VoicebotService instance."""
        if 'voicebot_service' not in self._instances:
            self._instances['voicebot_service'] = VoicebotService(
                speech_recognition=self.get_speech_recognition_adapter(),
                rag=self.get_rag_adapter(),
                llm=self.get_llm_adapter(),
                tts=self.get_tts_adapter(),
                conversation_service=self.get_conversation_service()
            )
        return self._instances['voicebot_service']
    
    def get_voicebot_controller(self) -> VoicebotController:
        """Get or create VoicebotController instance."""
        if 'voicebot_controller' not in self._instances:
            self._instances['voicebot_controller'] = VoicebotController(
                voicebot_service=self.get_voicebot_service()
            )
        return self._instances['voicebot_controller']


# Global container instance
container = Container()