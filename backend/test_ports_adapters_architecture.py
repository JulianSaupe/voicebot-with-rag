#!/usr/bin/env python3
"""Test script to verify the ports and adapters architecture implementation."""

import asyncio
import sys
import os

# Add the parent directory to the Python path so we can import backend module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.internal.container import container
from backend.internal.domain.models.audio_transcription import AudioTranscription
from backend.internal.domain.models.conversation_context import ConversationContext
from backend.internal.domain.models.voice_response import VoiceResponse


async def test_dependency_injection():
    """Test that the dependency injection container works correctly."""
    print("🧪 Testing dependency injection container...")
    
    # Test that we can get all services from the container
    conversation_service = container.get_conversation_service()
    speech_adapter = container.get_speech_recognition_adapter()
    llm_adapter = container.get_llm_adapter()
    rag_adapter = container.get_rag_adapter()
    tts_adapter = container.get_tts_adapter()
    voicebot_service = container.get_voicebot_service()
    voicebot_controller = container.get_voicebot_controller()
    
    print("✅ All services successfully created from container")
    
    # Test that services are singletons (same instance returned)
    assert conversation_service is container.get_conversation_service()
    assert voicebot_service is container.get_voicebot_service()
    print("✅ Singleton pattern working correctly")


async def test_domain_layer():
    """Test the domain layer without external dependencies."""
    print("\n🧪 Testing domain layer...")
    
    # Test AudioTranscription model
    transcription = AudioTranscription(text="Hello, how are you?", confidence=0.95)
    assert transcription.text == "Hello, how are you?"
    assert transcription.confidence == 0.95
    assert not transcription.is_empty()
    assert transcription.get_clean_text() == "Hello, how are you?"
    print("✅ AudioTranscription model working correctly")
    
    # Test ConversationContext model
    context = ConversationContext(
        user_query="What is AI?",
        relevant_documents=["AI is artificial intelligence", "Machine learning is a subset of AI"]
    )
    assert context.user_query == "What is AI?"
    assert context.has_relevant_context()
    assert len(context.relevant_documents) == 2
    context.add_to_history("User asked about AI")
    assert len(context.conversation_history) == 1
    print("✅ ConversationContext model working correctly")
    
    # Test VoiceResponse model
    response = VoiceResponse(text_content="AI stands for Artificial Intelligence", voice_settings="de-DE-Test")
    assert response.has_content()
    assert response.get_content_length() > 0
    assert not response.is_streaming()
    print("✅ VoiceResponse model working correctly")
    
    # Test ConversationService
    conversation_service = container.get_conversation_service()
    
    # Test transcription validation
    valid_transcription = AudioTranscription(text="Hello world")
    invalid_transcription = AudioTranscription(text="")
    assert conversation_service.validate_transcription(valid_transcription)
    assert not conversation_service.validate_transcription(invalid_transcription)
    
    # Test voice settings
    voice = conversation_service.prepare_response_settings("custom-voice")
    default_voice = conversation_service.prepare_response_settings("")
    assert voice == "custom-voice"
    assert default_voice == "de-DE-Chirp3-HD-Charon"
    
    print("✅ ConversationService working correctly")


async def test_ports_structure():
    """Test the ports structure (input/output)."""
    print("\n🧪 Testing ports structure...")
    
    # Test that input ports exist
    from backend.internal.ports.input.voicebot_use_case_port import VoicebotUseCasePort
    assert hasattr(VoicebotUseCasePort, 'transcribe_audio')
    assert hasattr(VoicebotUseCasePort, 'generate_voice_response')
    assert hasattr(VoicebotUseCasePort, 'generate_streaming_voice_response')
    print("✅ Input ports properly defined")
    
    # Test that output ports exist
    from backend.internal.ports.output.speech_recognition_port import SpeechRecognitionPort
    from backend.internal.ports.output.llm_port import LLMPort
    from backend.internal.ports.output.rag_port import RAGPort
    from backend.internal.ports.output.tts_port import TTSPort
    
    assert hasattr(SpeechRecognitionPort, 'transcribe_audio')
    assert hasattr(LLMPort, 'generate_response')
    assert hasattr(RAGPort, 'retrieve_relevant_documents')
    assert hasattr(TTSPort, 'synthesize_speech')
    print("✅ Output ports properly defined")


async def test_adapters_structure():
    """Test the adapters structure (driven/driving)."""
    print("\n🧪 Testing adapters structure...")
    
    # Test that driven adapters implement output ports
    from backend.internal.adapters.driven.google_speech_adapter import GoogleSpeechAdapter
    from backend.internal.adapters.driven.gemini_llm_adapter import GeminiLLMAdapter
    from backend.internal.adapters.driven.rag_adapter import RAGAdapter
    from backend.internal.adapters.driven.google_tts_adapter import GoogleTTSAdapter
    from backend.internal.ports.output.speech_recognition_port import SpeechRecognitionPort
    from backend.internal.ports.output.llm_port import LLMPort
    from backend.internal.ports.output.rag_port import RAGPort
    from backend.internal.ports.output.tts_port import TTSPort
    
    assert issubclass(GoogleSpeechAdapter, SpeechRecognitionPort)
    assert issubclass(GeminiLLMAdapter, LLMPort)
    assert issubclass(RAGAdapter, RAGPort)
    assert issubclass(GoogleTTSAdapter, TTSPort)
    print("✅ Driven adapters implement output ports correctly")
    
    # Test that driving adapters exist
    from backend.internal.adapters.driving.voicebot_controller import VoicebotController
    assert hasattr(VoicebotController, 'transcribe_audio')
    assert hasattr(VoicebotController, 'get_audio_stream')
    assert hasattr(VoicebotController, 'get_text_response')
    print("✅ Driving adapters properly structured")


async def test_application_layer():
    """Test the application layer services."""
    print("\n🧪 Testing application layer...")
    
    voicebot_service = container.get_voicebot_service()
    
    # Test that the service has all required dependencies
    assert voicebot_service.speech_recognition is not None
    assert voicebot_service.rag is not None
    assert voicebot_service.llm is not None
    assert voicebot_service.tts is not None
    assert voicebot_service.conversation_service is not None
    print("✅ VoicebotService dependencies properly injected")


async def main():
    """Run all tests."""
    print("🚀 Starting Ports and Adapters Architecture Tests\n")
    
    try:
        await test_dependency_injection()
        await test_domain_layer()
        await test_ports_structure()
        await test_adapters_structure()
        await test_application_layer()
        
        print("\n🎉 All tests passed! Ports and Adapters architecture is working correctly.")
        print("\n📋 Architecture Summary:")
        print("   ✅ Domain Layer: Pure business logic and models")
        print("   ✅ Ports: Input (driving) and Output (driven) interfaces")
        print("   ✅ Adapters: Driving (web) and Driven (external services)")
        print("   ✅ Application Layer: Use cases and orchestration")
        print("   ✅ Dependency Injection: Clean separation of concerns")
        print("   ✅ Ports and Adapters Pattern: Hexagonal architecture implemented")
        
        print("\n🏗️ Final Architecture Structure:")
        print("   📁 backend/domain/ (Business logic and models)")
        print("   📁 backend/ports/input/ (Driving ports - interfaces to drive the app)")
        print("   📁 backend/ports/output/ (Driven ports - interfaces for external services)")
        print("   📁 backend/adapters/driving/ (Web controllers)")
        print("   📁 backend/adapters/driven/ (External service adapters)")
        print("   📁 backend/application/ (Use cases and orchestration)")
        print("   📄 backend/container.py (Dependency injection)")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())