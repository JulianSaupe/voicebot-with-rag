import { WebSocketHandler, type WebSocketMessage } from './WebSocketHandler';

export interface TranscriptionEventData {
    text: string;
    confidence: number;
    id?: string;
    isFinal?: boolean;
}

export class MicrophoneInputService {
    private wsHandler: WebSocketHandler;
    private eventTarget: EventTarget;
    
    // Audio recording properties
    private audioStream: MediaStream | null = null;
    private audioContext: AudioContext | null = null;
    private audioWorkletNode: AudioWorkletNode | null = null;
    private sourceNode: MediaStreamAudioSourceNode | null = null;
    private isRecording: boolean = false;
    private isInitialized: boolean = false;
    private selectedVoice: string = 'de-DE-Chirp3-HD-Charon';

    constructor(wsHandler: WebSocketHandler) {
        this.wsHandler = wsHandler;
        this.eventTarget = new EventTarget();
        this.setupEventListeners();
    }

    private setupEventListeners(): void {
        // Listen for transcription messages
        this.wsHandler.addEventListener('transcription', (message: WebSocketMessage) => {
            this.handleTranscription(message);
        });

        // Listen for transcription error messages
        this.wsHandler.addEventListener('transcription_error', (message: WebSocketMessage) => {
            this.handleTranscriptionError(message);
        });

        // Listen for LLM response messages (forward to other services)
        this.wsHandler.addEventListener('llm_response', (message: WebSocketMessage) => {
            this.forwardLLMResponse(message);
        });

        // Listen for audio chunk messages (forward to audio playback service)
        // Backend sends "audio" type for speech, "audio_chunk" for text
        this.wsHandler.addEventListener('audio', (message: WebSocketMessage) => {
            this.forwardAudioChunk(message);
        });
        this.wsHandler.addEventListener('audio_chunk', (message: WebSocketMessage) => {
            this.forwardAudioChunk(message);
        });

        // Listen for audio end messages (forward to audio playback service)
        this.wsHandler.addEventListener('audio_end', (message: WebSocketMessage) => {
            this.forwardAudioEnd(message);
        });
    }

    private handleTranscription(message: WebSocketMessage): void {
        const eventData: TranscriptionEventData = {
            text: message.data?.transcription || (message as any).transcription || '',
            confidence: message.data?.confidence || (message as any).confidence || 0,
            id: message.id,
            isFinal: message.data?.is_final || (message as any).is_final || false
        };

        console.log('🎤 Transcription received:', eventData.text);

        // Dispatch custom event for components to listen to
        const customEvent = new CustomEvent('transcription', { 
            detail: eventData 
        });
        this.eventTarget.dispatchEvent(customEvent);

        // Also dispatch to window for backward compatibility
        window.dispatchEvent(customEvent);
    }

    private handleTranscriptionError(message: WebSocketMessage): void {
        const customEvent = new CustomEvent('transcription-error', { 
            detail: { 
                error: message.data?.error || 'Transcription error',
                id: message.id
            } 
        });
        this.eventTarget.dispatchEvent(customEvent);
        window.dispatchEvent(customEvent);
    }

    private forwardLLMResponse(message: WebSocketMessage): void {
        // Forward LLM response to other services/components
        // Backend sends llm_response directly in audio messages
        const llmText = message.data?.text || (message as any).llm_response || '';
        
        if (llmText) {
            const customEvent = new CustomEvent('llm-response', { 
                detail: {
                    text: llmText,
                    id: message.id || (message as any).id,
                    isComplete: message.data?.is_complete || false
                }
            });
            window.dispatchEvent(customEvent);
        }
    }

    private forwardAudioChunk(message: WebSocketMessage): void {
        // Forward audio chunk to audio playback service
        // Handle different backend formats: "data" field for speech, "chunk" field for text
        const audioData = {
            chunk: message.data?.chunk || (message as any).data || (message as any).chunk || []
        };
        
        const customEvent = new CustomEvent('audio-chunk', { 
            detail: audioData 
        });
        window.dispatchEvent(customEvent);

        // Also forward LLM response if present in audio message
        const llmText = (message as any).llm_response;
        if (llmText) {
            this.forwardLLMResponse(message);
        }
    }

    private forwardAudioEnd(message: WebSocketMessage): void {
        // Forward audio end to audio playback service
        const customEvent = new CustomEvent('audio-end', { 
            detail: message.data 
        });
        window.dispatchEvent(customEvent);
    }

    async initialize(): Promise<void> {
        if (this.isInitialized) {
            return;
        }

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
            this.audioContext = new AudioContext({ sampleRate: 48000 });

            // Load AudioWorklet processor
            await this.audioContext.audioWorklet.addModule('/src/lib/script/audio-processor.js');

            // Create audio source from microphone stream
            this.sourceNode = this.audioContext.createMediaStreamSource(this.audioStream);

            // Create AudioWorklet node for PCM processing
            this.audioWorkletNode = new AudioWorkletNode(this.audioContext, 'audio-processor');

            // Connect audio nodes
            this.sourceNode.connect(this.audioWorkletNode);

            this.isInitialized = true;
            console.log('🎤 Microphone access granted - PCM audio capture ready');
        } catch (error) {
            console.error('❌ Error accessing microphone or setting up audio processing:', error);
            throw error;
        }
    }

    startRecording(voice?: string): void {
        if (!this.isInitialized || !this.wsHandler.connected || this.isRecording || !this.audioWorkletNode) {
            console.warn('⚠️ Cannot start recording: not initialized, not connected, or already recording');
            return;
        }

        // Store the selected voice if provided
        if (voice) {
            this.selectedVoice = voice;
        }

        // Send voice selection message to backend
        const voiceMessage: WebSocketMessage = {
            type: 'voice_selection',
            data: { voice: this.selectedVoice },
            id: this.generateId()
        };
        this.wsHandler.sendMessage(voiceMessage);
        console.log('🎵 Voice selection sent to backend:', this.selectedVoice);

        // Handle PCM data from AudioWorklet
        this.audioWorkletNode.port.onmessage = (event) => {
            if (event.data.type === 'audioData' && this.wsHandler.connected && this.isRecording) {
                this.sendPCMData(event.data.data);
            }
        };

        this.isRecording = true;
        console.log('🎤 Recording started with PCM audio capture');

        // Dispatch recording started event
        const customEvent = new CustomEvent('recording-started');
        this.eventTarget.dispatchEvent(customEvent);
        window.dispatchEvent(customEvent);
    }

    stopRecording(): void {
        if (!this.isRecording) {
            return;
        }

        this.isRecording = false;
        console.log('🎤 Recording stopped');

        // Send stop recording message to backend
        const message: WebSocketMessage = {
            type: 'stop_recording',
            data: {},
            id: this.generateId()
        };
        this.wsHandler.sendMessage(message);

        // Dispatch recording stopped event
        const customEvent = new CustomEvent('recording-stopped');
        this.eventTarget.dispatchEvent(customEvent);
        window.dispatchEvent(customEvent);
    }

    private sendPCMData(pcmData: Float32Array): void {
        if (!this.wsHandler.connected) {
            return;
        }

        try {
            // Calculate audio level (RMS) from PCM data
            const audioLevel = this.calculateAudioLevel(pcmData);
            
            // Emit audio level event for visualization
            const audioLevelEvent = new CustomEvent('audio-level', {
                detail: { level: audioLevel }
            });
            this.eventTarget.dispatchEvent(audioLevelEvent);
            window.dispatchEvent(audioLevelEvent);

            // Convert Float32Array to regular array for JSON transmission
            const pcmArray = Array.from(pcmData);

            // Send PCM data in JSON format as expected by backend
            const message: WebSocketMessage = {
                type: 'pcm',
                data: pcmArray
            };

            this.wsHandler.sendMessage(message);
        } catch (error) {
            console.error('❌ Error sending PCM data:', error);
        }
    }

    private calculateAudioLevel(pcmData: Float32Array): number {
        // Calculate RMS (Root Mean Square) for audio level
        let sum = 0;
        for (let i = 0; i < pcmData.length; i++) {
            sum += pcmData[i] * pcmData[i];
        }
        const rms = Math.sqrt(sum / pcmData.length);
        
        // Convert to a more usable range (0-100) and apply some scaling
        const level = Math.min(100, rms * 1000);
        return level;
    }

    addEventListener(type: string, listener: EventListener): void {
        this.eventTarget.addEventListener(type, listener);
    }

    removeEventListener(type: string, listener: EventListener): void {
        this.eventTarget.removeEventListener(type, listener);
    }

    disconnect(): void {
        this.stopRecording();

        // Clean up audio resources
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

        this.isInitialized = false;
        this.isRecording = false;
    }

    private generateId(): string {
        return Date.now().toString() + Math.random().toString(36).substr(2, 9);
    }

    get connected(): boolean {
        return this.wsHandler.connected;
    }

    get initialized(): boolean {
        return this.isInitialized;
    }

    get recording(): boolean {
        return this.isRecording;
    }
}