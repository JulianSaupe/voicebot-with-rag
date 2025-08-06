import logging
import time
from typing import List, Tuple, Optional, Callable
import threading

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.audio import AudioClassifierOptions, AudioClassifier
from mediapipe.tasks.python.components.containers import AudioData


class VoiceActivityDetector:
    """Voice Activity Detection service using MediaPipe streaming VAD."""

    def __init__(self,
                 silence_threshold_ms: int = 200,
                 min_speech_duration_ms: int = 50,
                 sample_rate: int = 48000):
        """
        Initialize VAD service with MediaPipe streaming.
        
        Args:
            silence_threshold_ms: Milliseconds of silence before processing audio
            min_speech_duration_ms: Minimum speech duration before considering it valid
            sample_rate: Audio sample rate (should match frontend)
        """
        self.silence_threshold_ms = silence_threshold_ms
        self.min_speech_duration_ms = min_speech_duration_ms
        self.sample_rate = sample_rate

        # Audio buffer for PCM data (used for both VAD and transcription)
        self.pcm_buffer: List[np.ndarray] = []
        self.pre_speech_chunk_count = 50

        # Timing and state
        self.last_voice_time: float = 0
        self.first_voice_time: float = 0
        self.is_speaking = False
        self.speech_start_time: float = 0

        # Frame-based smoothing for more stable detection
        self.consecutive_voice_frames = 0
        self.consecutive_silence_frames = 0
        self.min_voice_frames = 1
        self.min_silence_frames = 1

        # MediaPipe streaming setup
        self.classifier = None
        self.total_samples_processed = 0
        self.classification_results = []
        self.results_lock = threading.Lock()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Initialize MediaPipe classifier with streaming mode
        self._initialize_classifier()

    def _initialize_classifier(self):
        """Initialize MediaPipe AudioClassifier for streaming VAD."""
        try:
            def result_callback(result, timestamp_ms: int):
                """Callback for MediaPipe streaming results."""
                with self.results_lock:
                    self.classification_results.append({
                        'result': result,
                        'timestamp_ms': timestamp_ms
                    })

            options = AudioClassifierOptions(
                base_options=BaseOptions(model_asset_path='backend/models/model.tflite'),
                max_results=5,
                running_mode=mp.tasks.audio.RunningMode.AUDIO_STREAM,
                result_callback=result_callback
            )

            self.classifier = AudioClassifier.create_from_options(options)

        except Exception as e:
            self.logger.error(f"Failed to initialize MediaPipe classifier: {e}")
            self.classifier = None

    def analyze_pcm_audio_activity(self, pcm_data: np.ndarray) -> bool:
        """
        Analyze raw PCM audio data for voice activity using MediaPipe.

        Args:
            pcm_data: Raw PCM audio data as numpy array (float32, normalized to [-1, 1])

        Returns:
            True if voice activity detected, False otherwise
        """
        if self.classifier is None:
            raise RuntimeError("MediaPipe classifier not initialized")

        try:
            # Create AudioData object for MediaPipe
            audio_data = AudioData.create_from_array(
                src=pcm_data.astype(np.float32),
                sample_rate=self.sample_rate
            )

            timestamp_ms = int(round(self.total_samples_processed / self.sample_rate, 6) * (10 ** 3))
            self.total_samples_processed += len(pcm_data)

            # Send to MediaPipe for streaming classification
            self.classifier.classify_async(audio_data, timestamp_ms)

            # Check recent classification results
            has_voice = self._check_recent_classifications()

            return has_voice

        except Exception as e:
            raise RuntimeError(f"Failed to analyze PCM audio for voice activity: {e}")

    def _check_recent_classifications(self) -> bool:
        """Check recent MediaPipe classification results for voice activity."""
        with self.results_lock:
            if not self.classification_results:
                return False

            # Look at the most recent result
            recent_result = self.classification_results[-1]['result']

            # Debug: Log all categories to understand what the model returns
            all_categories = []
            for classification in recent_result.classifications:
                for category in classification.categories:
                    all_categories.append(f"{category.category_name}:{category.score:.3f}")

            self.logger.debug(f"MediaPipe categories: {', '.join(all_categories)}")

            # Check for speech/voice categories in the classification
            for classification in recent_result.classifications:
                for category in classification.categories:
                    category_name = category.category_name.lower()
                    score = category.score

                    # Look for speech-related categories (adjust based on your model)
                    if category_name in ['speech', 'voice', 'talking', 'human voice', 'conversation'] and score > 0.5:
                        self.logger.debug(f"Speech detected: {category_name} = {score:.3f}")
                        return True

                    # Look for non-silence categories with high confidence
                    if category_name not in ['silence', 'quiet', 'background', 'background noise'] and score > 0.7:
                        self.logger.debug(f"Non-silence detected: {category_name} = {score:.3f}")
                        return True

                    # Alternative: Use the highest scoring category if it's not silence
                    if score > 0.8 and 'silence' not in category_name and 'quiet' not in category_name:
                        self.logger.debug(f"High confidence non-silence: {category_name} = {score:.3f}")
                        return True

            return False

    def process_audio_chunk(self, pcm_data: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Process PCM audio chunk for voice activity detection and transcription.
        
        Args:
            pcm_data: Raw PCM audio data for VAD analysis and transcription
            
        Returns:
            Tuple of (should_transcribe, accumulated_pcm_data)
        """
        current_time = time.time()

        # Analyze voice activity using PCM data
        has_voice = self.analyze_pcm_audio_activity(pcm_data)
        self.pcm_buffer.append(pcm_data)

        # Update voice activity state with smoothing
        if has_voice:
            self.last_voice_time = current_time
            self.consecutive_voice_frames += 1
            self.consecutive_silence_frames = 0

            if not self.is_speaking:
                if self.consecutive_voice_frames >= self.min_voice_frames:
                    self.is_speaking = True
                    self.first_voice_time = current_time
                    self.speech_start_time = current_time
                    self.pcm_buffer = self.pcm_buffer[-self.pre_speech_chunk_count:]
                    self.logger.info("🎤 Voice activity started")

            return False, None  # Continue accumulating
        else:
            # No voice detected
            self.consecutive_silence_frames += 1
            self.consecutive_voice_frames = 0

            if self.is_speaking:
                silence_duration = (current_time - self.last_voice_time) * 1000

                if (self.consecutive_silence_frames >= self.min_silence_frames and
                        silence_duration >= self.silence_threshold_ms):

                    # Check if we have enough speech duration
                    speech_duration = (self.last_voice_time - self.first_voice_time) * 1000

                    if speech_duration >= self.min_speech_duration_ms and self.pcm_buffer:
                        self.logger.info(f"🎤 Voice activity ended. Speech duration: {speech_duration:.0f}ms, "
                                         f"Silence: {silence_duration:.0f}ms")

                        # Combine all PCM chunks for transcription
                        combined_audio = np.concatenate(self.pcm_buffer)

                        # Reset state
                        self._reset_buffers()

                        return True, combined_audio
                    else:
                        self.logger.debug(f"Speech too short ({speech_duration:.0f}ms), continuing...")
                        self._reset_buffers()

            return False, None

    def force_process_buffer(self) -> Optional[np.ndarray]:
        """
        Force processing of any remaining audio in the buffer.
        Called when the audio stream ends.
        
        Returns:
            Combined PCM audio data if available, None otherwise
        """
        if not self.pcm_buffer:
            return None

        # Check if we have meaningful speech duration
        if self.is_speaking:
            current_time = time.time()
            speech_duration = (current_time - self.first_voice_time) * 1000

            if speech_duration >= self.min_speech_duration_ms:
                self.logger.info(f"🎤 Processing final buffer: {speech_duration:.0f}ms of speech")
                combined_audio = np.concatenate(self.pcm_buffer)
                self._reset_buffers()
                return combined_audio

        self.logger.debug("Final buffer too short, discarding")
        self._reset_buffers()
        return None

    def _reset_buffers(self):
        """Reset all buffers and state."""
        self.pcm_buffer.clear()
        self.is_speaking = False
        self.consecutive_voice_frames = 0
        self.consecutive_silence_frames = 0

        # Clear MediaPipe results
        with self.results_lock:
            self.classification_results.clear()

    def reset(self):
        """Reset the VAD service to initial state."""
        self.logger.info("🔄 Resetting VAD service")
        self._reset_buffers()
        self.last_voice_time = 0
        self.first_voice_time = 0
        self.speech_start_time = 0
        self.total_samples_processed = 0

    def __del__(self):
        """Cleanup MediaPipe classifier."""
        if self.classifier:
            try:
                self.classifier.close()
            except:
                pass
