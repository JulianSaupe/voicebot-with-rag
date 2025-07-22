import { WebSocketHandler, type WebSocketMessage } from './WebSocketHandler';

export interface TextInputOptions {
    voice?: string;
    language?: string;
}

export interface TextInputEventData {
    text: string;
    id?: string;
    isComplete?: boolean;
}

export class TextInputService {
    private wsHandler: WebSocketHandler;
    private eventTarget: EventTarget;

    constructor(wsHandler: WebSocketHandler) {
        this.wsHandler = wsHandler;
        this.eventTarget = new EventTarget();
        this.setupEventListeners();
    }

    private setupEventListeners(): void {
        // Listen for LLM response messages
        this.wsHandler.addEventListener('llm_response', (message: WebSocketMessage) => {
            this.handleLLMResponse(message);
        });

        // Listen for audio chunk messages (for audio playback service)
        this.wsHandler.addEventListener('audio_chunk', (message: WebSocketMessage) => {
            this.handleAudioChunk(message);
        });

        // Listen for audio end messages
        this.wsHandler.addEventListener('audio_end', (message: WebSocketMessage) => {
            this.handleAudioEnd(message);
        });

        // Listen for error messages
        this.wsHandler.addEventListener('error', (message: WebSocketMessage) => {
            this.handleError(message);
        });
    }

    private handleLLMResponse(message: WebSocketMessage): void {
        const eventData: TextInputEventData = {
            text: message.data?.text || '',
            id: message.id,
            isComplete: message.data?.is_complete || false
        };

        // Dispatch custom event for components to listen to
        const customEvent = new CustomEvent('llm-response', { 
            detail: eventData 
        });
        this.eventTarget.dispatchEvent(customEvent);

        // Also dispatch to window for backward compatibility
        window.dispatchEvent(customEvent);
    }

    private handleAudioChunk(message: WebSocketMessage): void {
        // Forward audio chunk to audio playback service via custom event
        // Handle backend format: "chunk" field directly, not nested in "data"
        const audioData = {
            chunk: message.data?.chunk || (message as any).chunk || []
        };
        
        const customEvent = new CustomEvent('audio-chunk', { 
            detail: audioData 
        });
        console.log('Dispatching audio chunk event, chunk length:', audioData.chunk.length);
        this.eventTarget.dispatchEvent(customEvent);
        window.dispatchEvent(customEvent);

        // Also forward LLM response if present in audio message
        const llmText = (message as any).llm_response;
        if (llmText) {
            this.handleLLMResponse({
                type: 'llm_response',
                data: { text: llmText, is_complete: false },
                id: message.id || (message as any).id
            } as WebSocketMessage);
        }
    }

    private handleAudioEnd(message: WebSocketMessage): void {
        // Forward audio end to audio playback service via custom event
        const customEvent = new CustomEvent('audio-end', { 
            detail: message.data 
        });
        this.eventTarget.dispatchEvent(customEvent);
        window.dispatchEvent(customEvent);
    }

    private handleError(message: WebSocketMessage): void {
        const customEvent = new CustomEvent('text-input-error', { 
            detail: { 
                error: message.data?.error || 'Unknown error',
                id: message.id
            } 
        });
        this.eventTarget.dispatchEvent(customEvent);
        window.dispatchEvent(customEvent);
    }

    async submitText(text: string, options: TextInputOptions = {}): Promise<void> {
        if (!this.wsHandler.connected) {
            throw new Error('WebSocket not connected');
        }

        if (!text.trim()) {
            throw new Error('Text cannot be empty');
        }

        const message: WebSocketMessage = {
            type: 'text_prompt',
            data: {
                text: text.trim(),
                voice: options.voice || 'de-DE-Chirp3-HD-Charon',
                language: options.language || 'de-DE'
            },
            id: this.generateId()
        };

        console.log('📝 Sending text prompt:', text);
        this.wsHandler.sendMessage(message);
    }

    addEventListener(type: string, listener: EventListener): void {
        this.eventTarget.addEventListener(type, listener);
    }

    removeEventListener(type: string, listener: EventListener): void {
        this.eventTarget.removeEventListener(type, listener);
    }

    private generateId(): string {
        return Date.now().toString() + Math.random().toString(36).substr(2, 9);
    }

    get connected(): boolean {
        return this.wsHandler.connected;
    }
}