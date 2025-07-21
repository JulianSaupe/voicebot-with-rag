// Audio service for handling all audio-related functionality
import {API_CONFIG} from './config';

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

// Submit prompt to API and process audio response
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

        // Connect to the API endpoint using the configured URL
        const response = await fetch(API_CONFIG.getAudioUrl(userPrompt, voice));

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Get the headers for audio configuration
        const sampleRate = parseInt(response.headers.get('Sample-Rate') || '24000');

        // Update UI
        updateSubtitle(`AI is responding to: "${userPrompt}"`);
        updateState({isListening: true});

        // Process the audio stream
        await processAudioStream(
            response,
            sampleRate,
            state,
            updateState,
            (errorMessage) => updateSubtitle(errorMessage),
            updateSubtitle
        );

        console.log('submitPrompt completed successfully');

    } catch (error: Error | any) {
        console.error('Error fetching audio:', error);
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