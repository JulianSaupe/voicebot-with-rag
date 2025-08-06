<script lang="ts">
    import {onMount, onDestroy} from 'svelte';
    import {browser} from '$app/environment';
    import {ServiceManager} from '$lib/script/ServiceManager';
    import ChatContainer from "$lib/components/ChatContainer.svelte";

    // Use Svelte 5 runes for reactive state
    let serviceManager: ServiceManager;
    let isConnected = $state(false);
    let isRecording = $state(false);
    let transcription = $state('');
    let confidence = $state(0);
    let error = $state('');
    let status = $state('Initializing...');

    // Chat state - using Svelte 5 $props() instead of export let
    let { messages = $bindable([]) }: {
        messages?: Array<{
            id: string;
            text: string;
            isUser: boolean;
            timestamp: Date;
        }>;
    } = $props();

    // Event handler functions
    function handleTranscription(event: CustomEvent) {
        const {text, confidence: conf} = event.detail;
        transcription = text;
        confidence = conf;
        error = '';

        messages = [
            ...messages,
            {
                id: Math.random().toString(),
                text,
                isUser: true,
                timestamp: new Date()
            }
        ];
    }

    function handleLLMResponse(event: CustomEvent) {
        const {text, id} = event.detail;
        const existingMessage = messages.find(msg => msg.id === id);

        if (existingMessage) {
            messages = messages.map(msg =>
                msg.id === id
                    ? {...msg, text: msg.text + " " + text}
                    : msg
            );
        } else {
            messages = [
                ...messages,
                {
                    id: id,
                    text,
                    isUser: false,
                    timestamp: new Date()
                }
            ];
        }
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
            // Initialize service manager with separate endpoints
            const baseHost = import.meta.env.VITE_API_BASE_URL
                ? new URL(import.meta.env.VITE_API_BASE_URL).host
                : 'localhost:8000';

            const speechWsUrl = `ws://${baseHost}/ws/speech`;
            const textWsUrl = `ws://${baseHost}/ws/text`;

            serviceManager = new ServiceManager({ speechWsUrl, textWsUrl });

            // Setup event listeners for transcription results (only in browser)
            window.addEventListener('transcription', handleTranscription as EventListener);
            window.addEventListener('transcription-error', handleTranscriptionError as EventListener);
            window.addEventListener('llm-response', handleLLMResponse as EventListener);

            // Initialize service manager (connects WebSocket and initializes microphone)
            await serviceManager.initialize();
            isConnected = serviceManager.connected;
            status = 'Connected and ready to record';

        } catch (err) {
            error = `Initialization failed: ${err}`;
            status = 'Error during initialization';
            console.error('❌ Service manager initialization failed:', err);
        }
    });

    onDestroy(() => {
        // Only cleanup if we're in the browser
        if (browser) {
            window.removeEventListener('transcription', handleTranscription as EventListener);
            window.removeEventListener('transcription-error', handleTranscriptionError as EventListener);
            window.removeEventListener('llm-response', handleLLMResponse as EventListener);

            if (serviceManager) {
                serviceManager.disconnect();
            }
        }
    });

    function toggleRecording() {
        // Guard against non-browser environment
        if (!browser || !serviceManager || !isConnected) return;

        if (isRecording) {
            serviceManager.stopRecording();
            status = 'Recording stopped';
        } else {
            serviceManager.startRecording();
            status = 'Recording... Speak now!';
            transcription = '';
            confidence = 0;
            error = '';
        }

        isRecording = !isRecording;
    }
</script>

<div class="speech-streaming-container">
    <div class="status-section">
        <p class="status">Status: <span class:connected={isConnected} class:error={error}>{status}</span></p>

        {#if error}
            <div class="error-message">
                <strong>Error:</strong> {error}
            </div>
        {/if}
    </div>

    <ChatContainer {messages}/>

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
</div>

<style>
    .speech-streaming-container {
        max-width: 100%;
        width: 100%;
        margin: 0 0;
        padding: 1rem;
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
        width: 100%;
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
        0% {
            opacity: 1;
        }
        50% {
            opacity: 0.7;
        }
        100% {
            opacity: 1;
        }
    }
</style>