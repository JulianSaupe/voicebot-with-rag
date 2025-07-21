// @ts-nocheck
class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferSize = 2048; // Process in chunks of 2048 samples
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        
        if (input.length > 0) {
            const inputChannel = input[0]; // Use first channel (mono)
            
            for (let i = 0; i < inputChannel.length; i++) {
                this.buffer[this.bufferIndex] = inputChannel[i];
                this.bufferIndex++;
                
                // When buffer is full, send it to main thread
                if (this.bufferIndex >= this.bufferSize) {
                    // Create a copy of the buffer to send
                    const bufferCopy = new Float32Array(this.buffer);
                    this.port.postMessage({
                        type: 'audioData',
                        data: bufferCopy
                    });
                    
                    // Reset buffer
                    this.bufferIndex = 0;
                }
            }
        }
        
        // Keep the processor alive
        return true;
    }
}

registerProcessor('audio-processor', AudioProcessor);