<script lang="ts">
    export let audioLevel: number = 0;
    export let isListening: boolean = false;

    // Calculate dynamic properties based on audio level
    $: bubbleScale = 1 + (audioLevel / 150); // More dramatic scaling
    $: glowIntensity = audioLevel / 100;
    $: pulseSpeed = Math.max(0.5, 2 - (audioLevel / 100));
    $: morphIntensity = audioLevel / 100; // For organic shape morphing
</script>

<div class="speech-bubble-container">
    <div
            class="speech-bubble"
            class:active={true}
            class:listening={isListening}
            style="
			transform: scale({bubbleScale}) rotate({audioLevel * 0.5}deg);
			--glow-intensity: {glowIntensity};
			--pulse-speed: {pulseSpeed}s;
			--morph-intensity: {morphIntensity};
		"
    >
        <div class="bubble-core">
            <div class="inner-glow"></div>
            <div class="sound-waves">
                {#each Array(5) as _, i}
                    <div
                            class="wave"
                            style="animation-delay: {i * 0.1}s; opacity: {audioLevel > i * 20 ? 1 : 0.3}"
                    ></div>
                {/each}
            </div>
        </div>

        <!-- Ambient particles -->
        <div class="particles">
            {#each Array(8) as _, i}
                <div
                        class="particle"
                        style="
						animation-delay: {i * 0.2}s;
						transform: rotate({i * 45}deg) translateX(100px);
					"
                ></div>
            {/each}
        </div>
    </div>

    <div class="status-indicator">
        {#if isListening}
            <span class="status-text listening">● Listening</span>
        {:else}
            <span class="status-text active">● Active</span>
        {/if}
    </div>
</div>

<style>
    .speech-bubble-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        padding: 4rem; /* More space around the bubble */
    }

    .speech-bubble {
        width: 250px;
        height: 250px;
        position: relative;
        transition: transform 0.15s ease-out;
        filter: drop-shadow(0 0 30px rgba(139, 92, 246, var(--glow-intensity, 0.15))) drop-shadow(0 0 50px rgba(79, 70, 229, calc(var(--glow-intensity, 0.15) * 0.7)));
        animation: float 6s ease-in-out infinite;
    }

    .bubble-core {
        width: 100%;
        height: 100%;
        border-radius: 50% 45% 55% 48% / 52% 47% 53% 48%;
        background: linear-gradient(135deg,
        rgba(255, 255, 255, 0.15) 0%,
        rgba(139, 92, 246, 0.25) 30%,
        rgba(79, 70, 229, 0.2) 60%,
        rgba(99, 102, 241, 0.15) 100%
        );
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        animation: idle-pulse 3s ease-in-out infinite, morph-idle 8s ease-in-out infinite;
        transition: border-radius 0.3s ease-out;
        backdrop-filter: blur(20px);
        box-shadow: 0 0 30px rgba(139, 92, 246, 0.15),
        0 0 60px rgba(79, 70, 229, 0.1),
        inset 0 0 60px rgba(255, 255, 255, 0.1);
    }

    .speech-bubble.active .bubble-core {
        background: linear-gradient(135deg,
        rgba(255, 255, 255, 0.2) 0%,
        rgba(139, 92, 246, 0.35) 30%,
        rgba(79, 70, 229, 0.3) 60%,
        rgba(99, 102, 241, 0.25) 100%
        );
        border-color: rgba(255, 255, 255, 0.3);
        border-radius: 45% 55% 50% 48% / 48% 52% 58% 42%;
        animation: active-pulse var(--pulse-speed) ease-in-out infinite, morph-active 6s ease-in-out infinite;
        box-shadow: 0 0 40px rgba(139, 92, 246, 0.2),
        0 0 80px rgba(79, 70, 229, 0.15),
        inset 0 0 80px rgba(255, 255, 255, 0.15);
    }

    .speech-bubble.listening .bubble-core {
        background: linear-gradient(135deg,
        rgba(255, 255, 255, 0.25) 0%,
        rgba(139, 92, 246, 0.45) 30%,
        rgba(79, 70, 229, 0.4) 60%,
        rgba(99, 102, 241, 0.35) 100%
        );
        border-color: rgba(255, 255, 255, 0.4);
        border-radius: 60% 40% 50% 45% / 45% 55% 50% 55%;
        animation: listening-pulse 0.8s ease-in-out infinite, morph-listening 4s ease-in-out infinite;
        box-shadow: 0 0 50px rgba(139, 92, 246, 0.3),
        0 0 100px rgba(79, 70, 229, 0.2),
        inset 0 0 100px rgba(255, 255, 255, 0.2);
    }

    .inner-glow {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 80%;
        height: 80%;
        transform: translate(-50%, -50%);
        border-radius: 50%;
        background: radial-gradient(circle,
        rgba(255, 255, 255, 0.5) 0%,
        rgba(139, 92, 246, 0.3) 40%,
        rgba(79, 70, 229, 0.2) 70%,
        transparent 90%
        );
        opacity: var(--glow-intensity, 0.6);
        animation: inner-glow 2s ease-in-out infinite alternate;
    }

    .sound-waves {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 60%;
        height: 60%;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
    }

    .wave {
        width: 4px;
        height: 20px;
        background: linear-gradient(to top,
        rgba(139, 92, 246, 0.9),
        rgba(99, 102, 241, 0.7),
        rgba(255, 255, 255, 0.5)
        );
        border-radius: 3px;
        animation: wave-animation 0.6s ease-in-out infinite alternate;
        transition: opacity 0.1s ease;
        box-shadow: 0 0 8px rgba(139, 92, 246, 0.3);
    }

    .wave:nth-child(1) {
        animation-delay: 0s;
        height: 20px;
    }

    .wave:nth-child(2) {
        animation-delay: 0.1s;
        height: 30px;
    }

    .wave:nth-child(3) {
        animation-delay: 0.2s;
        height: 40px;
    }

    .wave:nth-child(4) {
        animation-delay: 0.3s;
        height: 30px;
    }

    .wave:nth-child(5) {
        animation-delay: 0.4s;
        height: 20px;
    }

    .particles {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100%;
        height: 100%;
        pointer-events: none;
    }

    .particle {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 5px;
        height: 5px;
        background: radial-gradient(circle,
        rgba(255, 255, 255, 0.8) 0%,
        rgba(139, 92, 246, 0.6) 50%,
        rgba(79, 70, 229, 0.4) 100%
        );
        border-radius: 50%;
        animation: particle-float 4s ease-in-out infinite;
        opacity: 0;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
    }

    .speech-bubble.active .particle {
        opacity: 1;
    }

    .status-indicator {
        margin-top: 6rem;
        text-align: center;
    }

    .status-text {
        font-size: 0.9rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .status-text.active {
        color: #8b5cf6;
        background: linear-gradient(45deg, #8b5cf6, #6366f1);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .status-text.listening {
        color: #8b5cf6;
        background: linear-gradient(45deg, #8b5cf6, #6366f1, #4f46e5);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: listening-text 1s ease-in-out infinite;
    }

    /* Animations */
    @keyframes idle-pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.02);
        }
    }

    @keyframes active-pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }

    @keyframes listening-pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.1);
        }
    }

    @keyframes inner-glow {
        0% {
            opacity: 0.3;
        }
        100% {
            opacity: 0.7;
        }
    }

    @keyframes wave-animation {
        0% {
            transform: scaleY(0.5);
        }
        100% {
            transform: scaleY(1.2);
        }
    }

    @keyframes particle-float {
        0%, 100% {
            opacity: 0;
            transform: rotate(var(--rotation, 0deg)) translateX(80px) scale(0);
        }
        50% {
            opacity: 1;
            transform: rotate(var(--rotation, 0deg)) translateX(120px) scale(1);
        }
    }

    @keyframes listening-text {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.6;
        }
    }

    @keyframes morph-idle {
        0%, 100% {
            border-radius: 50% 45% 55% 48% / 52% 47% 53% 48%;
        }
        25% {
            border-radius: 48% 52% 50% 55% / 55% 50% 48% 52%;
        }
        50% {
            border-radius: 55% 48% 45% 50% / 48% 53% 52% 47%;
        }
        75% {
            border-radius: 47% 53% 52% 48% / 50% 48% 55% 52%;
        }
    }

    @keyframes morph-active {
        0%, 100% {
            border-radius: 45% 55% 50% 48% / 48% 52% 58% 42%;
        }
        25% {
            border-radius: 52% 48% 55% 45% / 55% 45% 50% 58%;
        }
        50% {
            border-radius: 48% 52% 45% 55% / 42% 58% 48% 52%;
        }
        75% {
            border-radius: 55% 45% 52% 48% / 58% 42% 55% 45%;
        }
    }

    @keyframes morph-listening {
        0%, 100% {
            border-radius: 60% 40% 50% 45% / 45% 55% 50% 55%;
        }
        20% {
            border-radius: 45% 55% 60% 40% / 55% 45% 60% 40%;
        }
        40% {
            border-radius: 50% 50% 45% 55% / 40% 60% 45% 55%;
        }
        60% {
            border-radius: 40% 60% 55% 45% / 55% 45% 55% 45%;
        }
        80% {
            border-radius: 55% 45% 40% 60% / 50% 50% 40% 60%;
        }
    }

    @keyframes float {
        0%, 100% {
            transform: translateY(0px) translateX(0px);
        }
        25% {
            transform: translateY(-10px) translateX(5px);
        }
        50% {
            transform: translateY(0px) translateX(-8px);
        }
        75% {
            transform: translateY(8px) translateX(3px);
        }
    }


    /* Responsive design */
    @media (max-width: 768px) {
        .speech-bubble-container {
            padding: 2rem;
        }

        .speech-bubble {
            width: 180px;
            height: 180px;
        }

        .status-text {
            font-size: 0.8rem;
        }
    }
</style> 