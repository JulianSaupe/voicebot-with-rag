export class SpeechStreamingService {
    private socket: WebSocket | null = null;
    private audioStream: MediaStream | null = null;
    private audioContext: AudioContext | null = null;
    private audioWorkletNode: AudioWorkletNode | null = null;
    private sourceNode: MediaStreamAudioSourceNode | null = null;
    private isRecording: boolean = false;
    private isConnected: boolean = false;

    // Audio playback properties
    private playbackAudioContext: AudioContext | null = null;
    private audioChunks: number[][] = [];
    private nextPlayTime: number = 0;
    private isStreamingAudio: boolean = false;
    private streamingEnded: boolean = false;
    private chunksPlayed: number = 0;

    constructor(private serverUrl: string = 'ws://localhost:8000/ws/speech') {
    }

    async initialize(): Promise<void> {
        try {
            // Request microphone with consistent settings
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 48000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Initialize AudioContext for PCM capture
            this.audioContext = new AudioContext({sampleRate: 48000});

            // Load AudioWorklet processor
            await this.audioContext.audioWorklet.addModule('/src/lib/script/audio-processor.js');

            // Create audio source from microphone stream
            this.sourceNode = this.audioContext.createMediaStreamSource(this.audioStream);

            // Create AudioWorklet node for PCM processing
            this.audioWorkletNode = new AudioWorkletNode(this.audioContext, 'audio-processor');

            // Connect audio nodes
            this.sourceNode.connect(this.audioWorkletNode);

            console.log('🎤 Microphone access granted - PCM audio capture ready');
        } catch (error) {
            console.error('❌ Error accessing microphone or setting up audio processing:', error);
            throw error;
        }
    }

    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            try {
                this.socket = new WebSocket(this.serverUrl);

                this.socket.onopen = () => {
                    console.log('🔌 WebSocket connected to backend VAD');
                    this.isConnected = true;
                    resolve();
                };

                this.socket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.handleWebSocketMessage(data);
                    } catch (error) {
                        console.error('❌ Error parsing WebSocket message:', error);
                    }
                };

                this.socket.onclose = (event) => {
                    console.log('🔌 WebSocket connection closed:', event);
                    this.isConnected = false;
                };

                this.socket.onerror = (error) => {
                    console.error('❌ WebSocket error:', error);
                    this.isConnected = false;
                    reject(error);
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    startRecording(): void {
        if (!this.audioStream || !this.socket || !this.isConnected || this.isRecording || !this.audioWorkletNode) {
            console.warn('⚠️ Cannot start recording: missing dependencies or already recording');
            return;
        }

        // Handle PCM data from AudioWorklet for both VAD and transcription
        this.audioWorkletNode.port.onmessage = (event) => {
            if (event.data.type === 'audioData' && this.socket && this.isConnected && this.isRecording) {
                this.sendPCMData(event.data.data);
            }
        };

        console.log('🎤 Recording started with PCM audio capture');
        this.isRecording = true;
    }

    stopRecording(): void {
        if (this.isRecording) {
            console.log('🎤 Recording stopped');
            this.isRecording = false;
        }
    }


    private sendPCMData(pcmData: Float32Array): void {
        try {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                // Send PCM data with a type identifier
                const message = {
                    type: 'pcm',
                    data: Array.from(pcmData),
                    sampleRate: 48000
                };
                this.socket.send(JSON.stringify(message));
                console.log(`🎵 PCM: Sent ${pcmData.length} samples for VAD and transcription`);
            }
        } catch (error) {
            console.error('❌ Error sending PCM data:', error);
        }
    }

    private handleWebSocketMessage(data: any): void {
        switch (data.type) {
            case 'transcription':
                this.handleTranscriptionMessage(data);
                break;
            case 'audio':
                this.handleAudioChunk(data);
                break;
            case 'audio_end':
                this.handleAudioEnd(data);
                break;
            case 'audio_error':
                this.handleAudioError(data);
                break;
            default:
                // Handle legacy messages without type field
                if (data.status === 'success' && data.transcription) {
                    this.handleTranscriptionMessage(data);
                } else if (data.status === 'error') {
                    console.error('❌ WebSocket error:', data.error);
                }
                break;
        }
    }

    private handleTranscriptionMessage(data: any): void {
        if (data.status === 'success') {
            console.log(`🎤 VAD Transcription: "${data.transcription}" (confidence: ${data.confidence})`);

            const event = new CustomEvent('transcription', {
                detail: {
                    text: data.transcription,
                    confidence: data.confidence,
                    languageCode: data.language_code
                }
            });
            window.dispatchEvent(event);
        } else if (data.status === 'error') {
            console.error('❌ Transcription error:', data.error);

            const event = new CustomEvent('transcription-error', {
                detail: {error: data.error}
            });
            window.dispatchEvent(event);
        }
    }

    private async handleAudioChunk(data: any): Promise<void> {
        console.log(`🔊 Received audio chunk ${data.chunk_number} (${data.data.length} bytes)`);

        // Extract and store LLM response if present (typically in first chunk)
        if (data.llm_response) {
            const event = new CustomEvent('llm-response', {
                detail: {
                    text: data.llm_response,
                    id: data.id,
                }
            });
            window.dispatchEvent(event);
        }

        // Store audio chunk
        this.audioChunks.push(data.data);

        // Start streaming playback if this is the first chunk
        if (!this.isStreamingAudio && this.audioChunks.length === 1) {
            console.log('🎵 Starting streaming audio playback');
            this.isStreamingAudio = true;
            this.streamingEnded = false;
            this.chunksPlayed = 0;
            await this.initializePlaybackContext();
        }

        // Play this chunk immediately if we're streaming
        if (this.isStreamingAudio) {
            await this.playAudioChunk(data.data);
        }

        // Dispatch event for UI updates
        const event = new CustomEvent('audio-chunk', {
            detail: {
                chunkNumber: data.chunk_number,
                dataSize: data.data.length,
                status: data.status,
                llmResponse: data.llm_response || null
            }
        });
        window.dispatchEvent(event);
    }

    private async handleAudioEnd(data: any): Promise<void> {
        console.log(`🏁 Audio streaming complete: ${data.total_chunks} chunks received`);

        try {
            // If we're not streaming, fall back to the old method
            if (!this.isStreamingAudio) {
                await this.playAudioChunks();
            } else {
                console.log('🎵 Streaming audio playback in progress, marking as ended');
                this.streamingEnded = true;
                // Check if all chunks have already been played
                if (this.chunksPlayed >= this.audioChunks.length) {
                    this.handleStreamingComplete();
                }
            }

            // Dispatch completion event
            const event = new CustomEvent('audio-complete', {
                detail: {
                    totalChunks: data.total_chunks,
                    status: data.status
                }
            });
            window.dispatchEvent(event);
        } catch (error) {
            console.error('❌ Error playing audio:', error);
            this.handleAudioError({error: `Audio playback failed: ${error}`});
        }
    }

    private handleAudioError(data: any): void {
        console.error('❌ Audio error:', data.error);

        // Clear any pending audio chunks and streaming state
        this.audioChunks = [];
        this.isStreamingAudio = false;
        this.streamingEnded = false;
        this.chunksPlayed = 0;
        this.nextPlayTime = 0;

        const event = new CustomEvent('audio-error', {
            detail: {error: data.error}
        });
        window.dispatchEvent(event);
    }

    private async initializePlaybackContext(): Promise<void> {
        if (!this.playbackAudioContext) {
            this.playbackAudioContext = new AudioContext({sampleRate: 24000}); // Google TTS uses 24kHz
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

        const event = new CustomEvent('audio-playback-complete');
        window.dispatchEvent(event);
    }

    private async playAudioChunks(): Promise<void> {
        if (this.audioChunks.length === 0) {
            console.warn('⚠️ No audio chunks to play');
            return;
        }

        try {
            // Initialize playback audio context if needed
            if (!this.playbackAudioContext) {
                this.playbackAudioContext = new AudioContext({sampleRate: 24000}); // Google TTS uses 24kHz
            }

            // Resume audio context if suspended
            if (this.playbackAudioContext.state === 'suspended') {
                await this.playbackAudioContext.resume();
            }

            // Combine all audio chunks into a single array
            const totalLength = this.audioChunks.reduce((sum, chunk) => sum + chunk.length, 0);
            const combinedAudio = new Int16Array(totalLength);

            let offset = 0;
            for (const chunk of this.audioChunks) {
                combinedAudio.set(chunk, offset);
                offset += chunk.length;
            }

            // Convert Int16 to Float32 for Web Audio API
            const floatArray = new Float32Array(combinedAudio.length);
            for (let i = 0; i < combinedAudio.length; i++) {
                floatArray[i] = combinedAudio[i] / 32768.0; // Convert from Int16 to Float32
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
                this.audioChunks = []; // Clear chunks after playback

                const event = new CustomEvent('audio-playback-complete');
                window.dispatchEvent(event);
            };

            console.log(`🔊 Playing audio: ${floatArray.length} samples at 24kHz`);
            source.start();

        } catch (error) {
            console.error('❌ Error in audio playback:', error);
            this.audioChunks = [];
            throw error;
        }
    }

    disconnect(): void {
        this.stopRecording();

        // Clean up recording AudioContext resources
        if (this.audioWorkletNode) {
            this.audioWorkletNode.disconnect();
            this.audioWorkletNode = null;
        }

        if (this.sourceNode) {
            this.sourceNode.disconnect();
            this.sourceNode = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }

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

        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }

        this.isConnected = false;
    }
}