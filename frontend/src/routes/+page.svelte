<script lang="ts">
    import {onMount, onDestroy} from 'svelte';
    import {browser} from '$app/environment';
    import ChatContainer from '$lib/components/ChatContainer.svelte';
    import SpeechBubble from '$lib/components/SpeechBubble.svelte';
    import {ServiceManager} from '$lib/script/ServiceManager';
    import SpeechTranscriptionModule from "$lib/components/SpeechTranscriptionModule.svelte";

    // UI state
    let userPrompt = '';
    let selectedVoice = 'de-DE-Chirp3-HD-Charon';
    let isProcessing = false;
    
    // Audio visualization state
    let audioLevel = 0;
    let isListening = false;

    // Chat state
    let messages: Array<{
        id: string;
        text: string;
        isUser: boolean;
        timestamp: Date;
    }> = [];

    // Service manager for text input
    let textServiceManager: ServiceManager;

    // Available voices
    const voices = [
        'de-DE-Chirp3-HD-Aoede',
        'de-DE-Chirp3-HD-Charon',
        'de-DE-Chirp3-HD-Leda',
        'de-DE-Chirp3-HD-Zephyr',
        'de-DE-Chirp3-HD-Fenrir'
    ];


    // Event handlers for LLM responses
    function handleLLMResponse(event: CustomEvent) {
        const {text, isComplete} = event.detail;

        // Add complete responses to chat
        if (isComplete && text) {
            addMessage(text, false);
        }
    }

    function handleTextInputError(event: CustomEvent) {
        const {error} = event.detail;
        isProcessing = false;
    }

    function handleAudioPlaybackComplete(event: CustomEvent) {
        isProcessing = false;
    }

    onMount(async () => {
        if (!browser) return;

        try {
            // Initialize service manager for text input with separate endpoints
            const baseHost = import.meta.env.VITE_API_BASE_URL
                ? new URL(import.meta.env.VITE_API_BASE_URL).host
                : 'localhost:8000';

            const speechWsUrl = `ws://${baseHost}/ws/speech`;
            const textWsUrl = `ws://${baseHost}/ws/text`;

            textServiceManager = new ServiceManager({speechWsUrl, textWsUrl});

            // Setup event listeners
            window.addEventListener('llm-response', handleLLMResponse as EventListener);
            window.addEventListener('text-input-error', handleTextInputError as EventListener);
            window.addEventListener('audio-playback-complete', handleAudioPlaybackComplete as EventListener);

            // Initialize service manager
            await textServiceManager.initialize();

        } catch (err) {
            console.error('❌ Text service initialization failed:', err);
        }
    });

    onDestroy(() => {
        if (browser) {
            window.removeEventListener('llm-response', handleLLMResponse as EventListener);
            window.removeEventListener('text-input-error', handleTextInputError as EventListener);
            window.removeEventListener('audio-playback-complete', handleAudioPlaybackComplete as EventListener);

            if (textServiceManager) {
                textServiceManager.disconnect();
            }
        }
    });

    const addMessage = (text: string, isUser: boolean) => {
        const newMessage = {
            id: Math.random().toString(),
            text,
            isUser,
            timestamp: new Date()
        };
        messages = [...messages, newMessage];
    };

    const submitPrompt = async () => {
        if (!userPrompt.trim() || isProcessing || !textServiceManager?.connected) return;

        isProcessing = true;

        // Add user message to chat
        addMessage(userPrompt.trim(), true);
        const currentPrompt = userPrompt.trim();
        userPrompt = ''; // Clear input immediately

        try {
            await textServiceManager.submitText(currentPrompt, {
                voice: selectedVoice
            });
        } catch (error) {
            console.error('❌ Error submitting text:', error);
            isProcessing = false;
        }
    };

    // Handle Enter key in the input field
    const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            submitPrompt();
        }
    };
</script>

<svelte:head>
    <title>AI Voicebot</title>
    <meta name="description" content="Modern AI Voicebot with Speech Recognition"/>
</svelte:head>

<main class="main-container">
    <div class="voice-selector">
        <select id="voice-select" bind:value={selectedVoice}>
            {#each voices as voice}
                <option value={voice}>{voice}</option>
            {/each}
        </select>
    </div>

    <div class="header">
        <h1 class="title">AI Voicebot</h1>
        <p class="subtitle">Voice Assistant</p>
    </div>

    <div class="app-layout">
        <!-- Central bubble area -->
        <div class="bubble-area">
            <SpeechBubble {audioLevel} {isListening} />
        </div>
        
        <!-- Right side chat area -->
        <div class="chat-area">
            <SpeechTranscriptionModule bind:messages={messages} bind:audioLevel={audioLevel} bind:isListening={isListening}/>
            
            <div class="controls">
                <div class="prompt-container">
                    <input
                            type="text"
                            bind:value={userPrompt}
                            placeholder="Ask a question or use microphone..."
                            class="prompt-input"
                            on:keydown={handleKeyDown}
                            disabled={isProcessing}
                    />
                    <button
                            class="submit-button"
                            on:click={submitPrompt}
                            disabled={!userPrompt.trim() || isProcessing}
                    >
                        {isProcessing ? 'Processing...' : 'Ask'}
                    </button>
                </div>
            </div>
        </div>
    </div>
</main>

<style>
    @import '$lib/style/voicebot.css';
</style>
