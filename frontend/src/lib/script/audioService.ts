// Audio service for handling all audio-related functionality
import {API_CONFIG} from './config';
import {SpeechStreamingService} from "$lib/script/speech_streaming_service";

// Types
export interface AudioState {
    audioContext: AudioContext | null;
    audioSource: AudioBufferSourceNode | null;
    audioChunks: Int16Array[];
    isPlaying: boolean;
    audioLevel: number;
    isListening: boolean;
    isProcessing: boolean;
}

// Initialize audio state
export function createAudioState(): AudioState {
    return {
        audioContext: null,
        audioSource: null,
        audioChunks: [],
        isPlaying: false,
        audioLevel: 0,
        isListening: false,
        isProcessing: false
    };
}

// Initialize AudioContext
export function initAudioContext(): AudioContext {
    return new (window.AudioContext || (window as any).webkitAudioContext)();
}

// Stop audio playback
export function stopAudio(state: AudioState): void {

    if (state.audioSource) {
        state.audioSource.stop();
        state.audioSource = null;
    }
    state.isPlaying = false;
    state.isListening = false;
    state.audioLevel = 0;
    state.isProcessing = false;

}

// Process streaming audio data
export async function processAudioStream(
    response: Response,
    sampleRate: number,
    state: AudioState,
    updateState: (updates: Partial<AudioState>) => void,
    onError: (message: string) => void,
    updateSubtitle: (subtitle: string) => void
): Promise<void> {
    try {
        // Get a reader for the stream
        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error('Unable to read response stream');
        }

        // Create an audio worklet for streaming audio
        if (!state.audioContext) {
            state.audioContext = initAudioContext();
        }

        // Create an analyzer for audio visualization
        const analyser = state.audioContext.createAnalyser();
        analyser.fftSize = 256;
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyser.connect(state.audioContext.destination);

        // Set up audio visualization
        state.isPlaying = true;
        updateState({isPlaying: true});

        let audioLevelCancelled = false;

        const updateAudioLevel = () => {
            if (audioLevelCancelled || !state.isPlaying) return;

            analyser.getByteFrequencyData(dataArray);

            // Calculate average level
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            const newAudioLevel = sum / bufferLength;
            updateState({audioLevel: newAudioLevel});

            // Request next frame if still playing
            if (state.isPlaying) {
                requestAnimationFrame(updateAudioLevel);
            }
        };

        // Start visualization
        updateAudioLevel();

        // Create a more continuous audio playback system using AudioBufferSourceNode
        // We'll use a buffer queue approach with careful scheduling
        const minBufferSize = 4096; // Minimum size for processing (smaller than before for lower latency)
        const maxQueueSize = 10;    // Maximum number of chunks to queue before processing
        let audioQueue: Float32Array[] = [];
        let isProcessing = false;
        let currentTime = state.audioContext.currentTime; // Start with current audio context time
        let isFirstPlay = true;
        let totalAudioDuration = 0; // Track total audio duration

        // Function to process and play audio from the queue
        const processQueue = async () => {
            if (isProcessing || audioQueue.length === 0) return;

            isProcessing = true;

            try {
                // Combine all available chunks into one buffer
                let totalLength = 0;
                audioQueue.forEach(chunk => totalLength += chunk.length);

                // Process if we have enough data or accumulated enough chunks
                // For the first chunk, we process immediately to start playbook faster
                if (totalLength >= minBufferSize || audioQueue.length >= maxQueueSize || isFirstPlay) {
                    const combinedBuffer = new Float32Array(totalLength);
                    let offset = 0;

                    audioQueue.forEach(chunk => {
                        combinedBuffer.set(chunk, offset);
                        offset += chunk.length;
                    });

                    // Create an audio buffer
                    const audioBuffer = state.audioContext!.createBuffer(1, combinedBuffer.length, sampleRate);
                    audioBuffer.getChannelData(0).set(combinedBuffer);

                    // Create and start a source
                    const source = state.audioContext!.createBufferSource();
                    source.buffer = audioBuffer;
                    source.connect(analyser);

                    // For the first play, start immediately
                    if (isFirstPlay) {
                        source.start(0);
                        currentTime = state.audioContext!.currentTime + audioBuffer.duration;
                        isFirstPlay = false;
                    } else {
                        // Schedule playback to maintain continuity
                        // Ensure we don't schedule in the past
                        const startTime = Math.max(currentTime, state.audioContext!.currentTime);
                        source.start(startTime);
                        currentTime = startTime + audioBuffer.duration;
                    }

                    // Track total audio duration
                    totalAudioDuration += audioBuffer.duration;

                    // Store the source to prevent garbage collection before it plays
                    state.audioSource = source;
                    updateState({audioSource: source});

                    // Clear the queue
                    audioQueue = [];
                }
            } catch (error) {
                console.error("Error processing audio queue:", error);
            } finally {
                isProcessing = false;
            }
        };

        // Read chunks from the stream
        while (true) {
            const {done, value} = await reader.read();

            if (done) {
                break;
            }

            // Convert the chunk to audio data
            const chunk = new Int16Array(value.buffer);

            // Convert Int16Array to Float32Array for Web Audio API
            const floatChunk = new Float32Array(chunk.length);
            for (let i = 0; i < chunk.length; i++) {
                // Convert from Int16 (-32768 to 32767) to Float32 (-1.0 to 1.0)
                floatChunk[i] = chunk[i] / 32768.0;
            }

            // Add to the queue
            audioQueue.push(floatChunk);

            // Process the queue
            await processQueue();

            // Small delay to allow other operations
            await new Promise(resolve => setTimeout(resolve, 10));
        }

        // Process any remaining audio in the queue
        while (audioQueue.length > 0) {
            await processQueue();
            await new Promise(resolve => setTimeout(resolve, 10));
        }

        // Calculate when all audio should finish playing
        const finishTime = state.audioContext!.currentTime + totalAudioDuration;
        const waitTime = Math.max(0, (finishTime - state.audioContext!.currentTime) * 1000);

        console.log(`Waiting ${waitTime}ms for audio to finish playing...`);

        // Wait for all audio to finish, then clean up
        if (waitTime > 0) {
            await new Promise(resolve => setTimeout(resolve, waitTime));
        }

        // Additional small buffer to ensure audio has fully finished
        await new Promise(resolve => setTimeout(resolve, 100));

        // When all audio has finished playing
        audioLevelCancelled = true;

        // Clear the subtitle when audio processing completes
        updateSubtitle('');

        // Reset all state using only the updateState function
        updateState({
            isPlaying: false,
            isListening: false,
            audioLevel: 0,
            isProcessing: false
        });

        console.log('Audio processing completed, isProcessing set to false');

    } catch (error: Error | any) {
        console.error('Error processing audio stream:', error);
        onError(`Error processing audio: ${error.message}`);

        // Clear error message after 5 seconds to avoid confusion
        setTimeout(() => {
            updateSubtitle('');
        }, 5000);

        // Reset state using only the updateState function
        updateState({
            isPlaying: false,
            isListening: false,
            isProcessing: false
        });

        console.log('Audio processing error, isProcessing set to false');
    }
}

// Submit prompt to API and process audio response via WebSocket
export async function submitPrompt(
    userPrompt: string,
    state: AudioState,
    updateState: (updates: Partial<AudioState>) => void,
    updateSubtitle: (subtitle: string) => void,
    voice?: string
): Promise<void> {
    if (!userPrompt.trim() || !state.audioContext) return;

    try {
        // Set processing state using updateState function
        updateState({isProcessing: true});

        stopAudio(state);
        state.audioChunks = [];
        updateState({audioChunks: []});

        // Clear any previous error messages when starting new operation
        updateSubtitle(`Processing: "${userPrompt}"`);

        // Connect to the WebSocket endpoint
        const websocket = new WebSocket(API_CONFIG.getTextWebSocketUrl());
        const speechStreamingService = new SpeechStreamingService();

        await new Promise<void>((resolve, reject) => {
            let audioQueue: Int16Array[] = [];
            let isProcessingQueue = false;
            let totalAudioDuration = 0;
            let audioLevelCancelled = false;
            const sampleRate = 24000; // Default sample rate from backend

            websocket.onopen = () => {
                console.log('WebSocket connected for text input');

                // Send text input message
                const message = {
                    type: 'text_input',
                    text: userPrompt,
                    voice: voice || 'de-DE-Chirp3-HD-Charon'
                };

                websocket.send(JSON.stringify(message));
                updateSubtitle(`AI is responding to: "${userPrompt}"`);
                updateState({isListening: true});
            };

            websocket.onmessage = async (event) => {
                try {
                    const data = JSON.parse(event.data);
                    speechStreamingService.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('❌ Error parsing WebSocket message:', error);
                }
            };

            websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(new Error('WebSocket connection error'));
            };

            websocket.onclose = (event) => {
                if (event.code !== 1000) { // Not a normal closure
                    console.error('WebSocket closed unexpectedly:', event.code, event.reason);
                    reject(new Error(`WebSocket closed unexpectedly: ${event.reason}`));
                }
            };

            // Audio processing queue function (similar to original processAudioStream)
            async function processAudioQueue() {
                if (isProcessingQueue || audioQueue.length === 0) return;

                isProcessingQueue = true;

                try {
                    while (audioQueue.length > 0) {
                        const audioChunk = audioQueue.shift()!;

                        // Convert Int16Array to Float32Array for Web Audio API
                        const floatArray = new Float32Array(audioChunk.length);
                        for (let i = 0; i < audioChunk.length; i++) {
                            floatArray[i] = audioChunk[i] / 32768.0; // Convert from int16 to float32
                        }

                        // Create audio buffer
                        const audioBuffer = state.audioContext!.createBuffer(1, floatArray.length, sampleRate);
                        audioBuffer.copyToChannel(floatArray, 0);

                        // Create and configure audio source
                        const source = state.audioContext!.createBufferSource();
                        const gainNode = state.audioContext!.createGain();
                        const analyser = state.audioContext!.createAnalyser();

                        source.buffer = audioBuffer;
                        source.connect(gainNode);
                        gainNode.connect(analyser);
                        analyser.connect(state.audioContext!.destination);

                        // Configure analyser for audio level visualization
                        analyser.fftSize = 256;
                        const bufferLength = analyser.frequencyBinCount;
                        const dataArray = new Uint8Array(bufferLength);

                        // Start playing audio
                        const startTime = state.audioContext!.currentTime + totalAudioDuration;
                        source.start(startTime);

                        totalAudioDuration += audioBuffer.duration;

                        // Update audio level visualization
                        if (!audioLevelCancelled) {
                            const updateAudioLevel = () => {
                                if (audioLevelCancelled) return;

                                analyser.getByteFrequencyData(dataArray);
                                let sum = 0;
                                for (let i = 0; i < bufferLength; i++) {
                                    sum += dataArray[i];
                                }
                                const average = sum / bufferLength;
                                const normalizedLevel = Math.min(average / 128.0, 1.0);

                                updateState({audioLevel: normalizedLevel});

                                if (state.audioContext!.currentTime < startTime + audioBuffer.duration) {
                                    requestAnimationFrame(updateAudioLevel);
                                }
                            };

                            if (state.audioContext!.currentTime >= startTime - 0.1) {
                                updateAudioLevel();
                            } else {
                                setTimeout(() => updateAudioLevel(), (startTime - state.audioContext!.currentTime - 0.1) * 1000);
                            }
                        }

                        // Small delay between processing chunks
                        await new Promise(resolve => setTimeout(resolve, 10));
                    }
                } finally {
                    isProcessingQueue = false;
                }
            }
        });

        console.log('submitPrompt completed successfully');

    } catch (error: Error | any) {
        console.error('Error in WebSocket audio processing:', error);
        updateSubtitle(`Error: ${error.message}`);
        updateState({isListening: false});

        // Clear error message after 5 seconds to avoid confusion
        setTimeout(() => {
            updateSubtitle('');
        }, 5000);

        // Reset processing state using updateState function
        updateState({isProcessing: false});

        console.log('submitPrompt error, isProcessing set to false');
    }
}