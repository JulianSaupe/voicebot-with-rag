<script lang="ts">
    import MessageBubble from './MessageBubble.svelte';
    
    export let messages: Array<{
        id: string;
        text: string;
        isUser: boolean;
        timestamp: Date;
    }> = [];
    
    let chatContainer: HTMLElement;
    
    // Auto-scroll to bottom when new messages are added
    $: if (messages.length > 0 && chatContainer) {
        setTimeout(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 100);
    }
</script>

<div class="chat-container" bind:this={chatContainer}>
    {#if messages.length === 0}
        <div class="empty-state">
            <div class="empty-icon">💬</div>
            <p>Start a conversation by typing a message or using the microphone</p>
        </div>
    {:else}
        {#each messages as message (message.id)}
            <MessageBubble 
                text={message.text} 
                isUser={message.isUser} 
                timestamp={message.timestamp}
            />
        {/each}
    {/if}
</div>

<style>
    .chat-container {
        width: 900px;
        max-width: 900px;
        height: 400px;
        overflow-y: auto;
        padding: 1rem;
        background: rgba(20, 20, 20, 0.6);
        border-radius: 16px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        margin-bottom: 2rem;
        scroll-behavior: smooth;
    }
    
    .chat-container::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: rgba(139, 92, 246, 0.5);
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: rgba(139, 92, 246, 0.7);
    }
    
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: rgba(255, 255, 255, 0.6);
        text-align: center;
    }
    
    .empty-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.7;
    }
    
    .empty-state p {
        font-size: 1.1rem;
        margin: 0;
        max-width: 300px;
        line-height: 1.5;
    }
</style>