<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	
	// Using Svelte 5 $props() instead of export let
	let { enabled = false, label = 'Toggle', disabled = false }: {
		enabled?: boolean;
		label?: string;
		disabled?: boolean;
	} = $props();
	
	const dispatch = createEventDispatcher();
	
	const handleToggle = () => {
		if (!disabled) {
			enabled = !enabled;
			dispatch('toggle', { enabled });
		}
	};
</script>

<div class="toggle-container">
	<label class="toggle-label" class:disabled>
		<span class="label-text">{label}</span>
		<button
			class="toggle-switch"
			class:enabled
			class:disabled
			on:click={handleToggle}
			aria-pressed={enabled}
			aria-label={label}
			type="button"
		>
			<div class="switch-track">
				<div class="switch-thumb">
					<div class="thumb-glow"></div>
				</div>
				<div class="track-glow"></div>
			</div>
			<div class="switch-indicator">
				{#if enabled}
					<svg 
						class="icon icon-on" 
						viewBox="0 0 24 24" 
						fill="none" 
						stroke="currentColor" 
						stroke-width="2"
					>
						<path d="M9 12l2 2 4-4"/>
					</svg>
				{:else}
					<svg 
						class="icon icon-off" 
						viewBox="0 0 24 24" 
						fill="none" 
						stroke="currentColor" 
						stroke-width="2"
					>
						<path d="M18 6L6 18M6 6l12 12"/>
					</svg>
				{/if}
			</div>
		</button>
	</label>
</div>

<style>
	.toggle-container {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.toggle-label {
		display: flex;
		align-items: center;
		gap: 1rem;
		cursor: pointer;
		user-select: none;
		transition: opacity 0.2s ease;
	}

	.toggle-label.disabled {
		cursor: not-allowed;
		opacity: 0.5;
	}

	.label-text {
		font-size: 1rem;
		color: #ffffff;
		font-weight: 500;
		letter-spacing: 0.02em;
	}

	.toggle-switch {
		position: relative;
		width: 60px;
		height: 32px;
		border: none;
		background: transparent;
		cursor: pointer;
		padding: 0;
		transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
	}

	.toggle-switch.disabled {
		cursor: not-allowed;
	}

	.switch-track {
		position: relative;
		width: 100%;
		height: 100%;
		background: rgba(68, 68, 68, 0.8);
		border: 2px solid rgba(139, 92, 246, 0.3);
		border-radius: 20px;
		transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
		overflow: hidden;
		backdrop-filter: blur(10px);
	}

	.toggle-switch.enabled .switch-track {
		background: rgba(139, 92, 246, 0.2);
		border-color: rgba(139, 92, 246, 0.8);
		box-shadow: 
			0 0 15px rgba(139, 92, 246, 0.3),
			inset 0 0 10px rgba(139, 92, 246, 0.1);
	}

	.track-glow {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: linear-gradient(90deg, 
			transparent 0%, 
			rgba(139, 92, 246, 0.1) 50%, 
			transparent 100%
		);
		opacity: 0;
		transition: opacity 0.3s ease;
	}

	.toggle-switch.enabled .track-glow {
		opacity: 1;
		animation: track-pulse 2s ease-in-out infinite;
	}

	.switch-thumb {
		position: absolute;
		top: 4px;
		left: 4px;
		width: 24px;
		height: 24px;
		background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
		border-radius: 50%;
		transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
		box-shadow: 
			0 2px 4px rgba(0, 0, 0, 0.2),
			0 0 0 1px rgba(0, 0, 0, 0.1);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.toggle-switch.enabled .switch-thumb {
		transform: translateX(24px);
		background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
		box-shadow: 
			0 2px 8px rgba(139, 92, 246, 0.4),
			0 0 0 1px rgba(139, 92, 246, 0.2);
	}

	.thumb-glow {
		position: absolute;
		top: -2px;
		left: -2px;
		right: -2px;
		bottom: -2px;
		border-radius: 50%;
		background: radial-gradient(circle, 
			rgba(139, 92, 246, 0.4) 0%, 
			transparent 70%
		);
		opacity: 0;
		transition: opacity 0.3s ease;
	}

	.toggle-switch.enabled .thumb-glow {
		opacity: 1;
		animation: thumb-glow 1.5s ease-in-out infinite;
	}

	.switch-indicator {
		position: absolute;
		top: 50%;
		left: 8px;
		transform: translateY(-50%);
		width: 16px;
		height: 16px;
		transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
		pointer-events: none;
	}

	.toggle-switch.enabled .switch-indicator {
		left: 36px;
	}

	.icon {
		width: 12px;
		height: 12px;
		color: #666;
		transition: all 0.3s ease;
	}

	.toggle-switch.enabled .icon {
		color: #ffffff;
	}

	.icon-on {
		opacity: 0;
		transform: scale(0.8);
	}

	.toggle-switch.enabled .icon-on {
		opacity: 1;
		transform: scale(1);
	}

	.icon-off {
		opacity: 1;
		transform: scale(1);
	}

	.toggle-switch.enabled .icon-off {
		opacity: 0;
		transform: scale(0.8);
	}

	/* Hover effects */
	.toggle-switch:hover:not(.disabled) .switch-track {
		border-color: rgba(139, 92, 246, 0.6);
		box-shadow: 0 0 10px rgba(139, 92, 246, 0.2);
	}

	.toggle-switch:hover:not(.disabled) .switch-thumb {
		transform: scale(1.05) translateX(0);
	}

	.toggle-switch.enabled:hover:not(.disabled) .switch-thumb {
		transform: scale(1.05) translateX(24px);
	}

	/* Focus effects */
	.toggle-switch:focus-visible {
		outline: 2px solid rgba(139, 92, 246, 0.5);
		outline-offset: 4px;
		border-radius: 20px;
	}

	/* Animations */
	@keyframes track-pulse {
		0%, 100% {
			opacity: 0.3;
		}
		50% {
			opacity: 0.7;
		}
	}

	@keyframes thumb-glow {
		0%, 100% {
			opacity: 0.5;
			transform: scale(1);
		}
		50% {
			opacity: 1;
			transform: scale(1.1);
		}
	}

	/* Responsive design */
	@media (max-width: 768px) {
		.label-text {
			font-size: 0.9rem;
		}
		
		.toggle-switch {
			width: 50px;
			height: 28px;
		}
		
		.switch-thumb {
			top: 4px;
			left: 4px;
			width: 20px;
			height: 20px;
		}
		
		.toggle-switch.enabled .switch-thumb {
			transform: translateX(18px);
		}
		
		.switch-indicator {
			left: 7px;
		}
		
		.toggle-switch.enabled .switch-indicator {
			left: 27px;
		}
		
		.icon {
			width: 10px;
			height: 10px;
		}
		
		.toggle-switch.enabled:hover:not(.disabled) .switch-thumb {
			transform: scale(1.05) translateX(18px);
		}
	}
</style> 