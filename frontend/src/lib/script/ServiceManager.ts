import { WebSocketHandler } from './WebSocketHandler';
import { TextInputService } from './TextInputService';
import { MicrophoneInputService } from './MicrophoneInputService';
import { AudioPlaybackService } from './AudioPlaybackService';

export interface ServiceManagerOptions {
    speechWsUrl: string;
    textWsUrl: string;
}

export class ServiceManager {
    private readonly speechWsHandler: WebSocketHandler;
    private readonly textWsHandler: WebSocketHandler;
    private readonly textInputService: TextInputService;
    private readonly microphoneInputService: MicrophoneInputService;
    private readonly audioPlaybackService: AudioPlaybackService;
    private isInitialized: boolean = false;

    constructor(options: ServiceManagerOptions) {
        // Initialize separate WebSocket handlers for speech and text
        this.speechWsHandler = new WebSocketHandler(options.speechWsUrl);
        this.textWsHandler = new WebSocketHandler(options.textWsUrl);
        
        // Initialize services with appropriate WebSocket handlers
        this.textInputService = new TextInputService(this.textWsHandler);
        this.microphoneInputService = new MicrophoneInputService(this.speechWsHandler);
        this.audioPlaybackService = new AudioPlaybackService();
    }

    async initialize(): Promise<void> {
        if (this.isInitialized) {
            return;
        }

        try {
            // Connect both WebSocket handlers
            await Promise.all([
                this.speechWsHandler.connect(),
                this.textWsHandler.connect()
            ]);
            console.log('🔌 Both WebSocket connections established (speech & text)');

            // Initialize microphone
            await this.microphoneInputService.initialize();
            console.log('🎤 Microphone initialized');

            this.isInitialized = true;
            console.log('✅ ServiceManager initialized successfully');
        } catch (error) {
            console.error('❌ ServiceManager initialization failed:', error);
            throw error;
        }
    }

    // Text input methods
    async submitText(text: string, options?: { voice?: string; language?: string }): Promise<void> {
        return this.textInputService.submitText(text, options);
    }

    // Microphone input methods
    startRecording(): void {
        this.microphoneInputService.startRecording();
    }

    stopRecording(): void {
        this.microphoneInputService.stopRecording();
    }

    // Audio playback methods
    async playCompleteAudio(audioChunks: number[][]): Promise<void> {
        return this.audioPlaybackService.playCompleteAudio(audioChunks);
    }

    // Event listener methods for components
    addEventListener(service: 'text' | 'microphone' | 'audio', type: string, listener: EventListener): void {
        switch (service) {
            case 'text':
                this.textInputService.addEventListener(type, listener);
                break;
            case 'microphone':
                this.microphoneInputService.addEventListener(type, listener);
                break;
            case 'audio':
                this.audioPlaybackService.addEventListener(type, listener);
                break;
        }
    }

    removeEventListener(service: 'text' | 'microphone' | 'audio', type: string, listener: EventListener): void {
        switch (service) {
            case 'text':
                this.textInputService.removeEventListener(type, listener);
                break;
            case 'microphone':
                this.microphoneInputService.removeEventListener(type, listener);
                break;
            case 'audio':
                this.audioPlaybackService.removeEventListener(type, listener);
                break;
        }
    }

    // Status getters
    get connected(): boolean {
        return this.speechWsHandler.connected && this.textWsHandler.connected;
    }

    get speechConnected(): boolean {
        return this.speechWsHandler.connected;
    }

    get textConnected(): boolean {
        return this.textWsHandler.connected;
    }

    get initialized(): boolean {
        return this.isInitialized;
    }

    get microphoneInitialized(): boolean {
        return this.microphoneInputService.initialized;
    }

    get recording(): boolean {
        return this.microphoneInputService.recording;
    }

    get audioPlaying(): boolean {
        return this.audioPlaybackService.isPlaying;
    }

    // Cleanup method
    disconnect(): void {
        this.microphoneInputService.disconnect();
        this.audioPlaybackService.disconnect();
        this.speechWsHandler.disconnect();
        this.textWsHandler.disconnect();
        this.isInitialized = false;
        console.log('🔌 ServiceManager disconnected');
    }

    // Direct access to services (if needed for advanced use cases)
    get services() {
        return {
            speechWebSocket: this.speechWsHandler,
            textWebSocket: this.textWsHandler,
            textInput: this.textInputService,
            microphoneInput: this.microphoneInputService,
            audioPlayback: this.audioPlaybackService
        };
    }
}