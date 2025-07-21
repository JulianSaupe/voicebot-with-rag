<script lang="ts">
    export let text: string;
    export let isUser: boolean;
    export let timestamp: Date;
    
    // Format timestamp for display
    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };
</script>

<div class="message-wrapper" class:user={isUser} class:llm={!isUser}>
    <div class="message-bubble" class:user-bubble={isUser} class:llm-bubble={!isUser}>
        <div class="message-content">
            {text}
        </div>
        <div class="message-timestamp">
            {formatTime(timestamp)}
        </div>
    </div>
    {#if !isUser}
        <div class="avatar llm-avatar">🤖</div>
    {:else}
        <div class="avatar user-avatar">👤</div>
    {/if}
</div>

<style>
    .message-wrapper {
        display: flex;
        margin-bottom: 1rem;
        align-items: flex-end;
        gap: 0.75rem;
        animation: slideIn 0.3s ease-out;
    }
    
    .message-wrapper.user {
        flex-direction: row-reverse;
        justify-content: flex-start;
    }
    
    .message-wrapper.llm {
        flex-direction: row;
        justify-content: flex-start;
    }
    
    .message-bubble {
        max-width: 70%;
        padding: 1rem 1.25rem;
        border-radius: 18px;
        position: relative;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        word-wrap: break-word;
        line-height: 1.5;
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        color: white;
        border-bottom-right-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .llm-bubble {
        background: rgba(30, 30, 30, 0.9);
        color: #ffffff;
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-bottom-left-radius: 6px;
    }
    
    .message-content {
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .message-timestamp {
        font-size: 0.75rem;
        opacity: 0.7;
        text-align: right;
    }
    
    .llm-bubble .message-timestamp {
        color: rgba(255, 255, 255, 0.6);
    }
    
    .user-bubble .message-timestamp {
        color: rgba(255, 255, 255, 0.8);
    }
    
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        flex-shrink: 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    .llm-avatar {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.8) 0%, rgba(79, 70, 229, 0.8) 100%);
        border: 1px solid rgba(139, 92, 246, 0.4);
    }
    
    .user-avatar {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.8) 0%, rgba(5, 150, 105, 0.8) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .message-bubble {
            max-width: 85%;
            padding: 0.875rem 1rem;
        }
        
        .avatar {
            width: 28px;
            height: 28px;
            font-size: 0.875rem;
        }
        
        .message-wrapper {
            gap: 0.5rem;
        }
    }
</style>