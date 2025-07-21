<script lang="ts">
    import {onMount} from 'svelte';
    import ChatContainer from '$lib/components/ChatContainer.svelte';
    import SubtitleDisplay from '$lib/components/SubtitleDisplay.svelte';
    import * as AudioService from '$lib/script/audioService';
    import * as SpeechService from '$lib/script/speechService';
    import SpeechTranscriptionModule from "$lib/components/SpeechTranscriptionModule.svelte";

    // UI state
    let currentSubtitle = '';
    let userPrompt = '';
    let selectedVoice = 'de-DE-Chirp3-HD-Charon';

    // Chat state
    let messages: Array<{
        id: string;
        text: string;
        isUser: boolean;
        timestamp: Date;
    }> = [];

    // Speech state
    let speechState = SpeechService.createSpeechState();
    $: isMicrophoneEnabled = speechState.isMicrophoneEnabled;
    $: isStreaming = speechState.isStreaming;

    // Available voices
    const voices = [
        'de-DE-Chirp3-HD-Aoede',
        'de-DE-Chirp3-HD-Charon',
        'de-DE-Chirp3-HD-Leda',
        'de-DE-Chirp3-HD-Zephyr',
        'de-DE-Chirp3-HD-Fenrir'
    ];

    // Audio state
    let audioState = AudioService.createAudioState();
    $: isProcessing = audioState.isProcessing;

    // Update audio state helper function
    const updateAudioState = (updates: Partial<AudioService.AudioState>) => {
        // Create a new object to ensure reactivity
        audioState = {...audioState, ...updates};
    };

    // Update subtitle helper function
    const updateSubtitle = (text: string) => {
        currentSubtitle = text;
    };

    onMount(() => {
        // Initialize AudioContext
        audioState.audioContext = AudioService.initAudioContext();
        updateAudioState(audioState);

        // Initialize voicebot as enabled
        updateSubtitle('Voicebot ready. Enter your question...');

        return () => {
            AudioService.stopAudio(audioState);
        };
    });

    const addMessage = (text: string, isUser: boolean) => {
        const newMessage = {
            id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
            text,
            isUser,
            timestamp: new Date()
        };
        messages = [...messages, newMessage];
    };

    const submitPrompt = async () => {
        if (!userPrompt.trim() || isProcessing) return;

        // Add user message to chat
        addMessage(userPrompt.trim(), true);
        const currentPrompt = userPrompt.trim();
        userPrompt = ''; // Clear input immediately

        // Custom subtitle update function that also adds LLM response to chat
        const updateSubtitleAndChat = (text: string) => {
            updateSubtitle(text);
            // Only add to chat if it's a complete response (not intermediate states)
            if (text && !text.includes('Processing') && !text.includes('ready')) {
                addMessage(text, false);
            }
        };

        await AudioService.submitPrompt(
            currentPrompt,
            audioState,
            updateAudioState,
            updateSubtitleAndChat,
            selectedVoice
        );
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

    <div class="chatbot-container">
        <SpeechTranscriptionModule/>

        <div class="controls">
            <div class="prompt-container">
                <input
                        type="text"
                        bind:value={userPrompt}
                        placeholder="Ask a question or use microphone..."
                        class="prompt-input"
                        on:keydown={handleKeyDown}
                        disabled={audioState.isProcessing}
                />
                <button
                        class="submit-button"
                        on:click={submitPrompt}
                        disabled={!userPrompt.trim() || audioState.isProcessing}
                >
                    {audioState.isProcessing ? 'Processing...' : 'Ask'}
                </button>
            </div>
        </div>
    </div>

    <SubtitleDisplay {currentSubtitle}/>
</main>

<style>
    @import '$lib/style/voicebot.css';
</style>
