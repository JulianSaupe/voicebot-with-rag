<script lang="ts">
    import {onMount} from 'svelte';
    import SpeechBubble from '$lib/SpeechBubble.svelte';
    import SubtitleDisplay from '$lib/SubtitleDisplay.svelte';
    import * as AudioService from '$lib/audioService';
    import * as SpeechService from '$lib/speechService';
    import SpeechTranscriptionModule from "$lib/SpeechTranscriptionModule.svelte";

    // UI state
    let currentSubtitle = '';
    let userPrompt = '';
    let selectedVoice = 'de-DE-Chirp3-HD-Charon';

    // Speech state
    let speechState = SpeechService.createSpeechState();
    $: isMicrophoneEnabled = speechState.isMicrophoneEnabled;
    $: isRecording = speechState.isRecording;
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

        // Initialize voicebot as enabled
        updateSubtitle('Voicebot ready. Enter your question...');

        return () => {
            AudioService.stopAudio(audioState);
        };
    });

    const submitPrompt = async () => {
        if (!userPrompt.trim() || isProcessing) return;

        await AudioService.submitPrompt(
            userPrompt,
            audioState,
            updateAudioState,
            updateSubtitle,
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

    // Speech state update helper function
    const updateSpeechState = (updates: Partial<SpeechService.SpeechState>) => {
        speechState = {...speechState, ...updates};
    };

    // Speech functionality using the service
    const handleToggleMicrophone = async () => {
        await SpeechService.toggleMicrophone(
            speechState, 
            updateSpeechState, 
            updateSubtitle,
            (transcription: string) => {
                // Update the input field with transcribed text
                userPrompt = transcription;
            }
        );
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
        <SpeechBubble {audioLevel} {isListening}/>
        <SpeechTranscriptionModule/>

        <div class="controls">
            <div class="microphone-controls">
                <button
                        class="microphone-toggle-button"
                        class:enabled={isMicrophoneEnabled}
                        class:streaming={isStreaming}
                        on:click={handleToggleMicrophone}
                >
                    {#if isStreaming}
                        🎤 Streaming Audio...
                    {:else if isMicrophoneEnabled}
                        🎤 Microphone On
                    {:else}
                        🎤 Enable Microphone
                    {/if}
                </button>
            </div>

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
