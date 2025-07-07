<script lang="ts">
    import {onMount} from 'svelte';
    import SpeechBubble from '$lib/SpeechBubble.svelte';
    import SubtitleDisplay from '$lib/SubtitleDisplay.svelte';
    import ToggleSwitch from '$lib/ToggleSwitch.svelte';
    import * as AudioService from '$lib/audioService';

    // UI state
    let isVoicebotEnabled = false;
    let currentSubtitle = '';
    let userPrompt = '';
    let selectedVoice = 'de-DE-Chirp3-HD-Charon';

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
    $: isListening = audioState.isListening;
    $: audioLevel = audioState.audioLevel;
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

        return () => {
            AudioService.stopAudio(audioState);
        };
    });

    const handleToggleVoicebot = (event: CustomEvent) => {
        // The component already updates isVoicebotEnabled via binding
        // We just need to react to the new state
        const enabled = event.detail.enabled;

        if (enabled) {
            updateSubtitle('Voicebot activated. Enter your question...');
            updateAudioState({isListening: false});
        } else {
            updateSubtitle('Voicebot disabled');
            updateAudioState({isListening: false});
            AudioService.stopAudio(audioState);
            setTimeout(() => {
                updateSubtitle('');
            }, 2000);
        }
    };

    const submitPrompt = async () => {
        if (!userPrompt.trim() || !isVoicebotEnabled || isProcessing) return;


        // Set isProcessing directly to ensure UI updates
        audioState.isProcessing = true;
        updateAudioState(audioState);


        try {
            await AudioService.submitPrompt(
                userPrompt,
                audioState,
                updateAudioState,
                updateSubtitle,
                selectedVoice
            );
        } finally {

            // Set isProcessing directly to ensure UI updates
            audioState.isProcessing = false;
            updateAudioState(audioState);

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

    <div class="chatbot-container">
        <SpeechBubble {audioLevel} {isListening} {isVoicebotEnabled}/>

        <div class="controls">
            <ToggleSwitch
                    bind:enabled={isVoicebotEnabled}
                    on:toggle={handleToggleVoicebot}
                    label="Enable Voicebot"
            />

            {#if isVoicebotEnabled}
                <div class="prompt-container">
                    <input
                            type="text"
                            bind:value={userPrompt}
                            placeholder="Ask a question..."
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
            {/if}
        </div>
    </div>

    <SubtitleDisplay {currentSubtitle}/>
</main>

<style>
    @import '$lib/style/voicebot.css';
</style>
