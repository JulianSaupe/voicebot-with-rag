/**
 * TranscriptionController - Frontend controller for managing WebSocket-based transcription processes
 * with cancellation support and keyboard shortcuts.
 */

class TranscriptionController {
    constructor(websocketUrl = 'ws://localhost:8000/ws/speech') {
        this.websocketUrl = websocketUrl;
        this.websocket = null;
        this.currentProcessId = null;
        this.isConnected = false;
        this.eventListeners = new Map();
        this.keyboardShortcutsEnabled = true;
        
        // Bind methods to preserve 'this' context
        this.handleKeyPress = this.handleKeyPress.bind(this);
        this.handleWebSocketMessage = this.handleWebSocketMessage.bind(this);
        this.handleWebSocketOpen = this.handleWebSocketOpen.bind(this);
        this.handleWebSocketClose = this.handleWebSocketClose.bind(this);
        this.handleWebSocketError = this.handleWebSocketError.bind(this);
        
        // Initialize keyboard shortcuts
        this.initializeKeyboardShortcuts();
    }

    /**
     * Initialize keyboard shortcuts for transcription control
     */
    initializeKeyboardShortcuts() {
        document.addEventListener('keydown', this.handleKeyPress);
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyPress(event) {
        if (!this.keyboardShortcutsEnabled) return;
        
        // Escape key - stop current transcription
        if (event.key === 'Escape') {
            event.preventDefault();
            this.stopTranscription();
        }
        
        // Ctrl+Shift+S - stop all transcriptions
        if (event.ctrlKey && event.shiftKey && event.key === 'S') {
            event.preventDefault();
            this.stopAllTranscriptions();
        }
    }

    /**
     * Connect to WebSocket server
     */
    async connect() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        try {
            this.websocket = new WebSocket(this.websocketUrl);
            
            this.websocket.onopen = this.handleWebSocketOpen;
            this.websocket.onmessage = this.handleWebSocketMessage;
            this.websocket.onclose = this.handleWebSocketClose;
            this.websocket.onerror = this.handleWebSocketError;
            
            // Wait for connection to be established
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('WebSocket connection timeout'));
                }, 5000);
                
                this.websocket.onopen = (event) => {
                    clearTimeout(timeout);
                    this.handleWebSocketOpen(event);
                    resolve();
                };
                
                this.websocket.onerror = (event) => {
                    clearTimeout(timeout);
                    this.handleWebSocketError(event);
                    reject(new Error('WebSocket connection failed'));
                };
            });
            
        } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
            throw error;
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.isConnected = false;
        this.currentProcessId = null;
    }

    /**
     * Start a new transcription process
     */
    async startTranscription(audioData, languageCode = 'de-DE', metadata = {}) {
        if (!this.isConnected) {
            throw new Error('WebSocket not connected');
        }

        if (this.currentProcessId) {
            console.warn('Transcription already in progress, stopping current process first');
            await this.stopTranscription();
        }

        const message = {
            type: 'start_transcription',
            audio_data: audioData,
            language_code: languageCode,
            metadata: metadata
        };

        this.websocket.send(JSON.stringify(message));
        console.log('🎤 Started transcription process');
    }

    /**
     * Stop the current transcription process
     */
    async stopTranscription(reason = 'Stopped by user') {
        if (!this.isConnected) {
            console.warn('WebSocket not connected');
            return;
        }

        if (!this.currentProcessId) {
            console.warn('No active transcription process to stop');
            return;
        }

        const message = {
            type: 'stop_transcription',
            process_id: this.currentProcessId,
            reason: reason
        };

        this.websocket.send(JSON.stringify(message));
        console.log('🛑 Stopping transcription process:', this.currentProcessId);
    }

    /**
     * Stop all active transcription processes
     */
    async stopAllTranscriptions(reason = 'All processes stopped by user') {
        if (!this.isConnected) {
            console.warn('WebSocket not connected');
            return;
        }

        const message = {
            type: 'stop_all_transcriptions',
            reason: reason
        };

        this.websocket.send(JSON.stringify(message));
        console.log('🛑 Stopping all transcription processes');
    }

    /**
     * Send PCM audio data (existing functionality)
     */
    sendPCMData(pcmData) {
        if (!this.isConnected) {
            console.warn('WebSocket not connected');
            return;
        }

        const message = {
            type: 'pcm',
            data: Array.from(pcmData)
        };

        this.websocket.send(JSON.stringify(message));
    }

    /**
     * Add event listener for transcription events
     */
    addEventListener(eventType, callback) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, []);
        }
        this.eventListeners.get(eventType).push(callback);
    }

    /**
     * Remove event listener
     */
    removeEventListener(eventType, callback) {
        if (this.eventListeners.has(eventType)) {
            const listeners = this.eventListeners.get(eventType);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * Emit event to registered listeners
     */
    emitEvent(eventType, data) {
        if (this.eventListeners.has(eventType)) {
            this.eventListeners.get(eventType).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${eventType}:`, error);
                }
            });
        }
    }

    /**
     * Handle WebSocket connection open
     */
    handleWebSocketOpen(event) {
        console.log('🔌 WebSocket connected to transcription service');
        this.isConnected = true;
        this.emitEvent('connected', { event });
    }

    /**
     * Handle WebSocket connection close
     */
    handleWebSocketClose(event) {
        console.log('🔌 WebSocket disconnected from transcription service');
        this.isConnected = false;
        this.currentProcessId = null;
        this.emitEvent('disconnected', { event });
    }

    /**
     * Handle WebSocket errors
     */
    handleWebSocketError(event) {
        console.error('❌ WebSocket error:', event);
        this.emitEvent('error', { event });
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'transcription_started':
                    this.currentProcessId = data.process_id;
                    console.log('🎤 Transcription started:', data.process_id);
                    this.emitEvent('transcriptionStarted', data);
                    break;
                    
                case 'transcription_progress':
                    console.log('⏳ Transcription progress:', data.message);
                    this.emitEvent('transcriptionProgress', data);
                    break;
                    
                case 'transcription_completed':
                    console.log('✅ Transcription completed:', data.transcription);
                    this.currentProcessId = null;
                    this.emitEvent('transcriptionCompleted', data);
                    break;
                    
                case 'transcription_stopped':
                    console.log('🛑 Transcription stopped:', data.reason);
                    this.currentProcessId = null;
                    this.emitEvent('transcriptionStopped', data);
                    break;
                    
                case 'transcription_cancelled':
                    console.log('❌ Transcription cancelled:', data.reason);
                    this.currentProcessId = null;
                    this.emitEvent('transcriptionCancelled', data);
                    break;
                    
                case 'all_transcriptions_stopped':
                    console.log('🛑 All transcriptions stopped:', data.stopped_count);
                    this.currentProcessId = null;
                    this.emitEvent('allTranscriptionsStopped', data);
                    break;
                    
                case 'transcription_error':
                    console.error('❌ Transcription error:', data.error);
                    this.emitEvent('transcriptionError', data);
                    break;
                    
                case 'transcription':
                    // Handle regular transcription results (existing functionality)
                    console.log('🎤 Transcription result:', data.transcription);
                    this.emitEvent('transcription', data);
                    break;
                    
                case 'audio':
                case 'audio_chunk':
                    // Handle audio chunks (existing functionality)
                    this.emitEvent('audioChunk', data);
                    break;
                    
                case 'audio_end':
                    // Handle audio stream end (existing functionality)
                    this.emitEvent('audioEnd', data);
                    break;
                    
                case 'audio_error':
                    // Handle audio errors (existing functionality)
                    console.error('❌ Audio error:', data.error);
                    this.emitEvent('audioError', data);
                    break;
                    
                default:
                    console.warn('Unknown message type:', data.type);
                    this.emitEvent('unknownMessage', data);
            }
            
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
            this.emitEvent('messageParseError', { error, rawData: event.data });
        }
    }

    /**
     * Enable or disable keyboard shortcuts
     */
    setKeyboardShortcutsEnabled(enabled) {
        this.keyboardShortcutsEnabled = enabled;
    }

    /**
     * Get current connection status
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            currentProcessId: this.currentProcessId,
            websocketState: this.websocket ? this.websocket.readyState : null
        };
    }

    /**
     * Clean up resources
     */
    destroy() {
        // Remove keyboard event listener
        document.removeEventListener('keydown', this.handleKeyPress);
        
        // Disconnect WebSocket
        this.disconnect();
        
        // Clear event listeners
        this.eventListeners.clear();
        
        console.log('🧹 TranscriptionController destroyed');
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TranscriptionController;
}

// Make available globally for direct script inclusion
if (typeof window !== 'undefined') {
    window.TranscriptionController = TranscriptionController;
}