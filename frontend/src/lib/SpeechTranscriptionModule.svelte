<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { browser } from '$app/environment';
    import { SpeechStreamingService } from '$lib/speech_streaming_service';

    let speechService: SpeechStreamingService;
    let isConnected = false;
    let isRecording = false;
    let transcription = '';
    let confidence = 0;
    let error = '';
    let status = 'Initializing...';

    // Event handler functions
    function handleTranscription(event: CustomEvent) {
        const { text, confidence: conf } = event.detail;
        transcription = text;
        confidence = conf;
        error = '';
    }

    function handleTranscriptionError(event: CustomEvent) {
        error = event.detail.error;
        console.error('❌ Transcription error:', error);
    }

    onMount(async () => {
        // Only initialize if we're in the browser
        if (!browser) {
            status = 'Loading...';
            return;
        }

        try {
            // Initialize speech service with your backend URL
            const wsUrl = import.meta.env.VITE_API_BASE_URL 
                ? `ws://${new URL(import.meta.env.VITE_API_BASE_URL).host}/ws/speech`
                : 'ws://localhost:8000/ws/speech';
            
            speechService = new SpeechStreamingService(wsUrl);
            
            // Setup event listeners for transcription results (only in browser)
            window.addEventListener('transcription', handleTranscription);
            window.addEventListener('transcription-error', handleTranscriptionError);
            
            // Initialize microphone access
            await speechService.initialize();
            status = 'Microphone ready, connecting to server...';
            
            // Connect to WebSocket
            await speechService.connect();
            isConnected = true;
            status = 'Connected and ready to record';
            
        } catch (err) {
            error = `Initialization failed: ${err}`;
            status = 'Error during initialization';
            console.error('❌ Speech service initialization failed:', err);
        }
    });

    onDestroy(() => {
        // Only cleanup if we're in the browser
        if (browser) {
            window.removeEventListener('transcription', handleTranscription);
            window.removeEventListener('transcription-error', handleTranscriptionError);
            
            if (speechService) {
                speechService.disconnect();
            }
        }
    });

    function toggleRecording() {
        // Guard against non-browser environment
        if (!browser || !speechService || !isConnected) return;

        if (isRecording) {
            speechService.stopRecording();
            status = 'Recording stopped';
        } else {
            speechService.startRecording();
            status = 'Recording... Speak now!';
            transcription = '';
            confidence = 0;
            error = '';
        }
        
        isRecording = !isRecording;
    }
</script>

<div class="speech-streaming-container">
    <h2>🎤 Real-time Speech Transcription</h2>
    
    <div class="status-section">
        <p class="status">Status: <span class:connected={isConnected} class:error={error}>{status}</span></p>
        
        {#if error}
            <div class="error-message">
                <strong>Error:</strong> {error}
            </div>
        {/if}
    </div>

    <div class="controls">
        <button 
            on:click={toggleRecording}
            disabled={!isConnected || !browser}
            class="record-button"
            class:recording={isRecording}
            class:disabled={!isConnected || !browser}
        >
            {#if !browser}
                🎤 Loading...
            {:else if isRecording}
                🔴 Stop Recording
            {:else}
                🎤 Start Recording
            {/if}
        </button>
    </div>

    {#if transcription}
        <div class="transcription-result">
            <h3>Transcription Result:</h3>
            <div class="transcription-text">"{transcription}"</div>
            <div class="confidence">Confidence: {(confidence * 100).toFixed(1)}%</div>
        </div>
    {/if}
</div>

<style>
    .speech-streaming-container {
        max-width: 600px;
        margin: 0 auto;
        padding: 2rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    .status-section {
        margin-bottom: 1.5rem;
    }

    .status {
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }

    .status span.connected {
        color: #28a745;
        font-weight: 600;
    }

    .status span.error {
        color: #dc3545;
        font-weight: 600;
    }

    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.375rem;
        border: 1px solid #f5c6cb;
    }

    .controls {
        text-align: center;
        margin-bottom: 2rem;
    }

    .record-button {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        min-width: 200px;
    }

    .record-button:hover:not(.disabled) {
        background-color: #0056b3;
        transform: translateY(-1px);
    }

    .record-button.recording {
        background-color: #dc3545;
        animation: pulse 1.5s ease-in-out infinite;
    }

    .record-button.recording:hover {
        background-color: #c82333;
    }

    .record-button.disabled {
        background-color: #6c757d;
        cursor: not-allowed;
        opacity: 0.6;
    }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }

    .transcription-result {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }

    .transcription-result h3 {
        margin-top: 0;
        color: #495057;
    }

    .transcription-text {
        font-size: 1.2rem;
        font-style: italic;
        color: #212529;
        margin: 1rem 0;
        padding: 1rem;
        background-color: white;
        border-radius: 0.375rem;
        border-left: 4px solid #007bff;
    }

    .confidence {
        font-size: 0.9rem;
        color: #6c757d;
    }
</style>