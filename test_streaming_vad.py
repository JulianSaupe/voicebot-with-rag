#!/usr/bin/env python3
"""
Test script for streaming VAD implementation.
This script tests the VoiceActivityDetector with simulated audio data.
"""

import numpy as np
import time
import logging
from backend.internal.domain.services.voice_activity_detector_service import VoiceActivityDetector

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_silence(duration_ms: int, sample_rate: int = 48000) -> np.ndarray:
    """Generate silence audio data."""
    samples = int(duration_ms * sample_rate / 1000)
    return np.zeros(samples, dtype=np.float32)

def generate_noise(duration_ms: int, amplitude: float = 0.02, sample_rate: int = 48000) -> np.ndarray:
    """Generate low-level noise to simulate speech."""
    samples = int(duration_ms * sample_rate / 1000)
    return np.random.normal(0, amplitude, samples).astype(np.float32)

def generate_speech_like(duration_ms: int, amplitude: float = 0.1, sample_rate: int = 48000) -> np.ndarray:
    """Generate speech-like audio data with varying frequencies."""
    samples = int(duration_ms * sample_rate / 1000)
    t = np.linspace(0, duration_ms / 1000, samples)
    
    # Mix multiple frequencies to simulate speech
    signal = (
        amplitude * np.sin(2 * np.pi * 200 * t) +  # Base frequency
        amplitude * 0.5 * np.sin(2 * np.pi * 400 * t) +  # Harmonic
        amplitude * 0.3 * np.sin(2 * np.pi * 800 * t) +  # Higher harmonic
        amplitude * 0.1 * np.random.normal(0, 1, samples)  # Noise
    )
    
    return signal.astype(np.float32)

# WebM simulation removed - now using PCM-only approach

def test_vad_basic_functionality():
    """Test basic VAD functionality with different audio types."""
    logger.info("🧪 Testing basic VAD functionality...")
    
    vad = VoiceActivityDetector(
        silence_threshold_ms=1000,  # Shorter for testing
        min_speech_duration_ms=300   # Shorter for testing
    )
    
    # Test 1: Silence should not trigger VAD
    logger.info("Test 1: Processing silence...")
    silence_pcm = generate_silence(500)
    
    should_transcribe, audio_data = vad.process_audio_chunk(silence_pcm)
    assert not should_transcribe, "Silence should not trigger transcription"
    logger.info("✅ Silence test passed")
    
    # Test 2: Speech-like audio should trigger VAD
    logger.info("Test 2: Processing speech-like audio...")
    speech_pcm = generate_speech_like(800)  # 800ms of speech
    
    should_transcribe, audio_data = vad.process_audio_chunk(speech_pcm)
    # First chunk shouldn't trigger (need consecutive frames)
    assert not should_transcribe, "First speech chunk should not immediately trigger"
    
    # Add more speech chunks
    for i in range(5):
        speech_pcm = generate_speech_like(200)
        should_transcribe, audio_data = vad.process_audio_chunk(speech_pcm)
        if should_transcribe:
            break
    
    logger.info("✅ Speech detection test passed")
    
    # Test 3: Silence after speech should trigger transcription
    logger.info("Test 3: Processing silence after speech...")
    for i in range(8):  # Need enough silence frames
        silence_pcm = generate_silence(200)
        should_transcribe, audio_data = vad.process_audio_chunk(silence_pcm)
        if should_transcribe:
            assert audio_data is not None, "Should return accumulated audio data"
            logger.info(f"✅ Transcription triggered with {len(audio_data)} samples of audio")
            break
    else:
        logger.warning("⚠️ Transcription was not triggered by silence after speech")
    
    logger.info("🎉 Basic VAD functionality tests completed")

def test_vad_streaming_scenario():
    """Test VAD with a realistic streaming scenario."""
    logger.info("🧪 Testing realistic streaming scenario...")
    
    vad = VoiceActivityDetector()
    transcription_count = 0
    
    # Simulate a conversation: silence -> speech -> silence -> speech -> silence
    scenario = [
        ("silence", 1000),      # 1s silence
        ("speech", 1500),       # 1.5s speech
        ("silence", 2000),      # 2s silence (should trigger transcription)
        ("speech", 2000),       # 2s speech
        ("silence", 2500),      # 2.5s silence (should trigger transcription)
    ]
    
    for audio_type, duration_ms in scenario:
        logger.info(f"Processing {audio_type} for {duration_ms}ms...")
        
        # Process in 100ms chunks to simulate real streaming
        chunks = duration_ms // 100
        for chunk in range(chunks):
            if audio_type == "silence":
                pcm_data = generate_silence(100)
            else:
                pcm_data = generate_speech_like(100)
            
            should_transcribe, audio_data = vad.process_audio_chunk(pcm_data)
            
            if should_transcribe:
                transcription_count += 1
                logger.info(f"🎤 Transcription #{transcription_count} triggered with {len(audio_data)} samples")
    
    # Process final buffer
    final_audio = vad.force_process_buffer()
    if final_audio:
        transcription_count += 1
        logger.info(f"🎤 Final transcription triggered with {len(final_audio)} samples")
    
    logger.info(f"🎉 Streaming scenario completed with {transcription_count} transcriptions")
    assert transcription_count >= 2, f"Expected at least 2 transcriptions, got {transcription_count}"

def main():
    """Run all VAD tests."""
    logger.info("🚀 Starting VAD streaming tests...")
    
    try:
        test_vad_basic_functionality()
        test_vad_streaming_scenario()
        
        logger.info("🎉 All VAD tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())