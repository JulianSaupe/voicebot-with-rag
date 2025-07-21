<script lang="ts">
	export let currentSubtitle: string = '';
	
	let displayText = '';
	let isVisible = false;
	
	// Handle subtitle changes with smooth transitions
	$: if (currentSubtitle) {
		showSubtitle(currentSubtitle);
	} else {
		hideSubtitle();
	}
	
	const showSubtitle = (text: string) => {
		if (text !== displayText) {
			isVisible = false;
			setTimeout(() => {
				displayText = text;
				isVisible = true;
			}, 150);
		}
	};
	
	const hideSubtitle = () => {
		isVisible = false;
		setTimeout(() => {
			displayText = '';
		}, 300);
	};
</script>

<div class="subtitle-container">
	<div 
		class="subtitle-display" 
		class:visible={isVisible && displayText}
		class:hidden={!isVisible || !displayText}
	>
		<div class="subtitle-background"></div>
		<p class="subtitle-text">{displayText}</p>
		<div class="subtitle-accent"></div>
	</div>
</div>

<style>
	.subtitle-container {
		position: fixed;
		bottom: 4rem;
		left: 50%;
		transform: translateX(-50%);
		z-index: 1000;
		max-width: 90vw;
		width: 100%;
		max-width: 600px;
	}

	.subtitle-display {
		position: relative;
		background: rgba(10, 10, 10, 0.85);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(139, 92, 246, 0.3);
		border-radius: 16px;
		padding: 1rem 1.5rem;
		margin: 0 auto;
		transform: translateY(100px);
		opacity: 0;
		transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
		box-shadow: 
			0 10px 30px rgba(0, 0, 0, 0.5),
			0 0 20px rgba(139, 92, 246, 0.15);
		overflow: hidden;
	}

	.subtitle-display.visible {
		transform: translateY(0);
		opacity: 1;
	}

	.subtitle-display.hidden {
		transform: translateY(50px);
		opacity: 0;
	}

	.subtitle-background {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: linear-gradient(135deg, 
			rgba(139, 92, 246, 0.05) 0%, 
			rgba(99, 102, 241, 0.03) 50%, 
			rgba(79, 70, 229, 0.05) 100%
		);
		border-radius: inherit;
	}

	.subtitle-text {
		position: relative;
		margin: 0;
		font-size: 1.1rem;
		line-height: 1.5;
		color: #ffffff;
		text-align: center;
		font-weight: 400;
		letter-spacing: 0.02em;
		z-index: 2;
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
	}

	.subtitle-accent {
		position: absolute;
		bottom: 0;
		left: 50%;
		transform: translateX(-50%);
		width: 60px;
		height: 2px;
		background: linear-gradient(90deg, 
			transparent 0%, 
			#8b5cf6 50%, 
			transparent 100%
		);
		border-radius: 1px;
		animation: accent-glow 2s ease-in-out infinite;
	}

	.subtitle-display.visible .subtitle-accent {
		animation: accent-slide-in 0.5s ease-out 0.2s both, 
				   accent-glow 2s ease-in-out infinite 0.7s;
	}

	/* Animations */
	@keyframes accent-slide-in {
		0% {
			width: 0;
			opacity: 0;
		}
		100% {
			width: 60px;
			opacity: 1;
		}
	}

	@keyframes accent-glow {
		0%, 100% {
			box-shadow: 0 0 5px rgba(139, 92, 246, 0.3);
		}
		50% {
			box-shadow: 0 0 15px rgba(139, 92, 246, 0.6);
		}
	}

	/* Responsive design */
	@media (max-width: 768px) {
		.subtitle-container {
			bottom: 2rem;
			max-width: 95vw;
		}
		
		.subtitle-display {
			padding: 0.8rem 1.2rem;
		}
		
		.subtitle-text {
			font-size: 1rem;
		}
		
		.subtitle-accent {
			width: 40px;
		}
	}

	@media (max-width: 480px) {
		.subtitle-text {
			font-size: 0.9rem;
		}
		
		.subtitle-display {
			padding: 0.7rem 1rem;
		}
	}
</style> 