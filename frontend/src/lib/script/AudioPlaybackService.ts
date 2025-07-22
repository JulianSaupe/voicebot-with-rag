export class AudioPlaybackService {
    private eventTarget: EventTarget;
    
    // Audio playback properties
    private playbackAudioContext: AudioContext | null = null;
    private audioChunks: number[][] = [];
    private nextPlayTime: number = 0;
    private isStreamingAudio: boolean = false;
    private streamingEnded: boolean = false;
    private chunksPlayed: number = 0;

    constructor() {
        this.eventTarget = new EventTarget();
        this.setupEventListeners();
    }

    private setupEventListeners(): void {
        // Listen for audio chunk events from other services
        window.addEventListener('audio-chunk', ((event: CustomEvent) => {
            this.handleAudioChunk(event.detail);
        }) as EventListener);

        // Listen for audio end events
        window.addEventListener('audio-end', ((event: CustomEvent) => {
            this.handleAudioEnd(event.detail);
        }) as EventListener);
    }

    private async handleAudioChunk(data: any): Promise<void> {
        if (!data || !data.chunk) {
            console.warn('⚠️ Invalid audio chunk data received');
            return;
        }

        console.log('🔊 Audio chunk received, length:', data.chunk.length);

        // Initialize playback context if needed
        if (!this.isStreamingAudio) {
            await this.initializePlaybackContext();
            this.isStreamingAudio = true;
            this.streamingEnded = false;
            this.chunksPlayed = 0;
            this.audioChunks = [];
        }

        // Store the chunk
        this.audioChunks.push(data.chunk);

        // Play the chunk immediately for streaming
        try {
            await this.playAudioChunk(data.chunk);
        } catch (error) {
            console.error('❌ Error playing audio chunk:', error);
        }
    }

    private async handleAudioEnd(data: any): Promise<void> {
        console.log('🔊 Audio streaming ended');
        this.streamingEnded = true;

        // If no chunks are currently playing, complete immediately
        if (this.chunksPlayed >= this.audioChunks.length) {
            this.handleStreamingComplete();
        }
    }

    private async initializePlaybackContext(): Promise<void> {
        if (!this.playbackAudioContext) {
            this.playbackAudioContext = new AudioContext({ sampleRate: 24000 }); // Google TTS uses 24kHz
        }

        // Resume audio context if suspended
        if (this.playbackAudioContext.state === 'suspended') {
            await this.playbackAudioContext.resume();
        }

        // Initialize the next play time to current time
        this.nextPlayTime = this.playbackAudioContext.currentTime;
    }

    private async playAudioChunk(chunkData: number[]): Promise<void> {
        if (!this.playbackAudioContext) {
            console.error('❌ Playback audio context not initialized');
            return;
        }

        try {
            // Convert Int16 to Float32 for Web Audio API
            const floatArray = new Float32Array(chunkData.length);
            for (let i = 0; i < chunkData.length; i++) {
                floatArray[i] = chunkData[i] / 32768.0; // Convert from Int16 to Float32
            }

            // Create audio buffer for this chunk
            const audioBuffer = this.playbackAudioContext.createBuffer(
                1, // mono
                floatArray.length,
                24000 // sample rate
            );

            audioBuffer.copyToChannel(floatArray, 0);

            // Create and schedule audio source
            const source = this.playbackAudioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.playbackAudioContext.destination);

            // Schedule playback at the next available time
            const currentTime = this.playbackAudioContext.currentTime;
            const playTime = Math.max(currentTime, this.nextPlayTime);

            source.start(playTime);

            // Update next play time for seamless continuation
            const chunkDuration = floatArray.length / 24000; // duration in seconds
            this.nextPlayTime = playTime + chunkDuration;

            console.log(`🔊 Scheduled audio chunk: ${floatArray.length} samples, playing at ${playTime.toFixed(3)}s, duration ${chunkDuration.toFixed(3)}s`);

            // Handle chunk completion
            source.onended = () => {
                this.chunksPlayed++;
                console.log(`🔊 Chunk completed: ${this.chunksPlayed}/${this.audioChunks.length}`);

                // Check if streaming is complete (all chunks received and played)
                if (this.streamingEnded && this.chunksPlayed >= this.audioChunks.length) {
                    this.handleStreamingComplete();
                }
            };

        } catch (error) {
            console.error('❌ Error playing audio chunk:', error);
            throw error;
        }
    }

    private handleStreamingComplete(): void {
        console.log('🔊 Streaming audio playback completed');
        this.isStreamingAudio = false;
        this.streamingEnded = false;
        this.chunksPlayed = 0;
        this.nextPlayTime = 0;
        this.audioChunks = []; // Clear chunks after playback

        // Dispatch completion event
        const event = new CustomEvent('audio-playback-complete');
        this.eventTarget.dispatchEvent(event);
        window.dispatchEvent(event);
    }

    // Method to play complete audio (for non-streaming scenarios)
    async playCompleteAudio(audioChunks: number[][]): Promise<void> {
        if (audioChunks.length === 0) {
            console.warn('⚠️ No audio chunks to play');
            return;
        }

        try {
            // Initialize playback audio context if needed
            if (!this.playbackAudioContext) {
                this.playbackAudioContext = new AudioContext({ sampleRate: 24000 });
            }

            // Resume audio context if suspended
            if (this.playbackAudioContext.state === 'suspended') {
                await this.playbackAudioContext.resume();
            }

            // Combine all audio chunks into a single array
            const totalLength = audioChunks.reduce((sum, chunk) => sum + chunk.length, 0);
            const combinedAudio = new Int16Array(totalLength);

            let offset = 0;
            for (const chunk of audioChunks) {
                combinedAudio.set(chunk, offset);
                offset += chunk.length;
            }

            // Convert Int16 to Float32 for Web Audio API
            const floatArray = new Float32Array(combinedAudio.length);
            for (let i = 0; i < combinedAudio.length; i++) {
                floatArray[i] = combinedAudio[i] / 32768.0;
            }

            // Create audio buffer
            const audioBuffer = this.playbackAudioContext.createBuffer(
                1, // mono
                floatArray.length,
                24000 // sample rate
            );

            audioBuffer.copyToChannel(floatArray, 0);

            // Create and play audio source
            const source = this.playbackAudioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.playbackAudioContext.destination);

            // Handle playback completion
            source.onended = () => {
                console.log('🔊 Audio playback completed');
                const event = new CustomEvent('audio-playback-complete');
                this.eventTarget.dispatchEvent(event);
                window.dispatchEvent(event);
            };

            console.log(`🔊 Playing audio: ${floatArray.length} samples at 24kHz`);
            source.start();

        } catch (error) {
            console.error('❌ Error in audio playback:', error);
            throw error;
        }
    }

    addEventListener(type: string, listener: EventListener): void {
        this.eventTarget.addEventListener(type, listener);
    }

    removeEventListener(type: string, listener: EventListener): void {
        this.eventTarget.removeEventListener(type, listener);
    }

    disconnect(): void {
        // Clean up playback AudioContext resources
        if (this.playbackAudioContext) {
            this.playbackAudioContext.close();
            this.playbackAudioContext = null;
        }

        // Clear audio playback state
        this.audioChunks = [];
        this.isStreamingAudio = false;
        this.streamingEnded = false;
        this.chunksPlayed = 0;
        this.nextPlayTime = 0;
    }

    get isPlaying(): boolean {
        return this.isStreamingAudio;
    }
}