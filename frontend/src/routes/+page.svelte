<script lang="ts">
	import { onMount } from 'svelte';
	import SpeechBubble from '$lib/SpeechBubble.svelte';
	import SubtitleDisplay from '$lib/SubtitleDisplay.svelte';
	import ToggleSwitch from '$lib/ToggleSwitch.svelte';

	let isVoicebotEnabled = false;
	let isListening = false;
	let currentSubtitle = '';
	let audioLevel = 0;

	// Mock audio level simulation for demo purposes
	let audioInterval: number;
	
	const startAudioSimulation = () => {
		audioInterval = setInterval(() => {
			if (isVoicebotEnabled && isListening) {
				audioLevel = Math.random() * 100;
			} else {
				audioLevel = 0;
			}
		}, 100);
	};

	const stopAudioSimulation = () => {
		if (audioInterval) {
			clearInterval(audioInterval);
		}
		audioLevel = 0;
	};

	const handleToggleVoicebot = (event: CustomEvent) => {
		// The component already updates isVoicebotEnabled via binding
		// We just need to react to the new state
		const enabled = event.detail.enabled;
		
		if (enabled) {
			currentSubtitle = 'Voicebot activated. Say something...';
			isListening = true;
			startAudioSimulation();
		} else {
			currentSubtitle = 'Voicebot disabled';
			isListening = false;
			stopAudioSimulation();
			setTimeout(() => {
				currentSubtitle = '';
			}, 2000);
		}
	};

	onMount(() => {
		return () => {
			stopAudioSimulation();
		};
	});

	// Mock conversation for demonstration
	const mockResponses = [
		"Hello! How can I help you today?",
		"That's an interesting question. Let me think about it.",
		"I understand what you're asking. Here's my response.",
		"Is there anything else you'd like to know?",
		"Thank you for chatting with me!"
	];

	let responseIndex = 0;

	const simulateResponse = () => {
		if (isVoicebotEnabled) {
			currentSubtitle = mockResponses[responseIndex % mockResponses.length];
			responseIndex++;
			isListening = true;
		}
	};

	// Simulate periodic responses when voicebot is active
	let responseInterval: number;
	
	$: if (isVoicebotEnabled) {
		responseInterval = setInterval(simulateResponse, 5000);
	} else if (responseInterval) {
		clearInterval(responseInterval);
	}
</script>

<svelte:head>
	<title>AI Voicebot</title>
	<meta name="description" content="Modern AI Voicebot with Speech Recognition" />
</svelte:head>

<main class="main-container">
	<div class="header">
		<h1 class="title">AI Voicebot</h1>
		<p class="subtitle">Futuristic Voice Assistant</p>
	</div>

	<div class="chatbot-container">
		<SpeechBubble {audioLevel} {isListening} {isVoicebotEnabled} />
		
		<div class="controls">
			<ToggleSwitch 
				bind:enabled={isVoicebotEnabled} 
				on:toggle={handleToggleVoicebot}
				label="Enable Voicebot"
			/>
		</div>
	</div>

	<SubtitleDisplay {currentSubtitle} />
</main>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2a2a2a 100%);
		color: #ffffff;
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		min-height: 100vh;
		overflow-x: hidden;
	}

	.main-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 100vh;
		padding: 2rem;
		background: radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.05) 0%, rgba(79, 70, 229, 0.03) 40%, transparent 70%);
	}

	.header {
		text-align: center;
		margin-bottom: 3rem;
		z-index: 2;
	}

	.title {
		font-size: 3.5rem;
		font-weight: 700;
		margin: 0;
		background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 50%, #c7d2fe 100%);
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
		letter-spacing: -0.02em;
	}

	.subtitle {
		font-size: 1.2rem;
		color: #888;
		margin: 0.5rem 0 0 0;
		font-weight: 300;
	}

	.chatbot-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		position: relative;
		z-index: 1;
	}

	.controls {
		margin-top: 3rem;
		z-index: 3;
	}

	@media (max-width: 768px) {
		.title {
			font-size: 2.5rem;
		}
		
		.subtitle {
			font-size: 1rem;
		}
		
		.main-container {
			padding: 1rem;
		}
	}


</style>
