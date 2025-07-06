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
    console.log("stopAudio - Before stopping audio:", state.isProcessing);

    if (state.audioSource) {
        state.audioSource.stop();
        state.audioSource = null;
    }
    state.isPlaying = false;
    state.isListening = false;
    state.audioLevel = 0;
    state.isProcessing = false;

    console.log("stopAudio - After setting isProcessing to false:", state.isProcessing);
}

// Process streaming audio data
export async function processAudioStream(
    response: Response,
    sampleRate: number,
    state: AudioState,
    updateState: (updates: Partial<AudioState>, source: string) => void,
    onError: (message: string) => void
): Promise<void> {
    console.log("Starting processAudioStream - isProcessing:", state.isProcessing);
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
        updateState({isPlaying: true}, "processAudioStream");

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
            updateState({audioLevel: newAudioLevel}, "updateAudioLevel");

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

        // Function to process and play audio from the queue
        const processQueue = async () => {
            if (isProcessing || audioQueue.length === 0) return;

            isProcessing = true;

            try {
                // Combine all available chunks into one buffer
                let totalLength = 0;
                audioQueue.forEach(chunk => totalLength += chunk.length);

                // Process if we have enough data or accumulated enough chunks
                // For the first chunk, we process immediately to start playback faster
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
                        console.log("Starting first audio chunk");
                    } else {
                        // Schedule playback to maintain continuity
                        // Ensure we don't schedule in the past
                        const startTime = Math.max(currentTime, state.audioContext!.currentTime);
                        source.start(startTime);
                        currentTime = startTime + audioBuffer.duration;
                        console.log(`Scheduled audio at ${startTime}, duration: ${audioBuffer.duration}`);
                    }

                    // Store the source to prevent garbage collection before it plays
                    state.audioSource = source;
                    updateState({audioSource: source}, "processQueue");

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
                console.log('Stream complete');
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

        // When all chunks are processed
        audioLevelCancelled = true;
        console.log("All chunks processed - Before setting isProcessing to false:", state.isProcessing);

        // Set isProcessing directly to ensure UI updates
        state.isProcessing = false;
        updateState({
            isPlaying: false,
            isListening: false,
            audioLevel: 0,
            isProcessing: false
        }, "processAudioStream");

        console.log("After setting isProcessing to false:", state.isProcessing);

    } catch (error) {
        console.error('Error processing audio stream:', error);
        onError(`Error processing audio: ${error.message}`);

        console.log("Error in processAudioStream - Before setting isProcessing to false:", state.isProcessing);

        // Set isProcessing directly to ensure UI updates
        state.isProcessing = false;
        updateState({
            isPlaying: false,
            isListening: false,
            isProcessing: false
        }, "processAudioStream");

        console.log("After setting isProcessing to false:", state.isProcessing);
    }
}

// Submit prompt to API and process audio response
export async function submitPrompt(
    userPrompt: string,
    state: AudioState,
    updateState: (updates: Partial<AudioState>, source: string) => void,
    updateSubtitle: (subtitle: string) => void
): Promise<void> {
    if (!userPrompt.trim() || !state.audioContext) return;

    console.log("submitPrompt - Initial state.isProcessing:", state.isProcessing);

    try {
        // Set isProcessing directly to ensure UI updates
        state.isProcessing = true;
        updateState({isProcessing: true}, "submitPrompt");
        console.log("After setting isProcessing to true:", state.isProcessing);

        stopAudio(state);
        state.audioChunks = [];
        updateState({audioChunks: []}, "submitPrompt");

        updateSubtitle(`Processing: "${userPrompt}"`);

        // Connect to the API endpoint using the configured URL
        const response = await fetch(API_CONFIG.getAudioUrl(userPrompt));

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Get the headers for audio configuration
        const sampleRate = parseInt(response.headers.get('Sample-Rate') || '24000');

        // Update UI
        updateSubtitle(`AI is responding to: "${userPrompt}"`);
        updateState({isListening: true}, "submitPrompt");

        // Process the audio stream
        await processAudioStream(
            response,
            sampleRate,
            state,
            updateState,
            (errorMessage) => updateSubtitle(errorMessage)
        );

    } catch (error) {
        console.error('Error fetching audio:', error);
        updateSubtitle(`Error: ${error.message}`);
        updateState({isListening: false}, "submitPrompt");
    } finally {
        console.log("submitPrompt finally - Before setting isProcessing to false:", state.isProcessing);

        // Set isProcessing directly to ensure UI updates
        state.isProcessing = false;
        updateState({isProcessing: false}, "submitPrompt");

        console.log("After setting isProcessing to false:", state.isProcessing);
    }
}
