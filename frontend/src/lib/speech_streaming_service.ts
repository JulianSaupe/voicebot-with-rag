export class SpeechStreamingService {
    private socket: WebSocket | null = null;
    private audioStream: MediaStream | null = null;
    private audioContext: AudioContext | null = null;
    private audioWorkletNode: AudioWorkletNode | null = null;
    private sourceNode: MediaStreamAudioSourceNode | null = null;
    private isRecording: boolean = false;
    private isConnected: boolean = false;

    constructor(private serverUrl: string = 'ws://localhost:8000/ws/speech') {
    }

    async initialize(): Promise<void> {
        try {
            // Request microphone with consistent settings
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 48000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Initialize AudioContext for PCM capture
            this.audioContext = new AudioContext({sampleRate: 48000});

            // Load AudioWorklet processor
            await this.audioContext.audioWorklet.addModule('/src/lib/audio-processor.js');

            // Create audio source from microphone stream
            this.sourceNode = this.audioContext.createMediaStreamSource(this.audioStream);

            // Create AudioWorklet node for PCM processing
            this.audioWorkletNode = new AudioWorkletNode(this.audioContext, 'audio-processor');

            // Connect audio nodes
            this.sourceNode.connect(this.audioWorkletNode);

            console.log('🎤 Microphone access granted - PCM audio capture ready');
        } catch (error) {
            console.error('❌ Error accessing microphone or setting up audio processing:', error);
            throw error;
        }
    }

    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            try {
                this.socket = new WebSocket(this.serverUrl);

                this.socket.onopen = () => {
                    console.log('🔌 WebSocket connected to backend VAD');
                    this.isConnected = true;
                    resolve();
                };

                this.socket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.handleTranscriptionResult(data);
                    } catch (error) {
                        console.error('❌ Error parsing WebSocket message:', error);
                    }
                };

                this.socket.onclose = (event) => {
                    console.log('🔌 WebSocket connection closed:', event);
                    this.isConnected = false;
                };

                this.socket.onerror = (error) => {
                    console.error('❌ WebSocket error:', error);
                    this.isConnected = false;
                    reject(error);
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    startRecording(): void {
        if (!this.audioStream || !this.socket || !this.isConnected || this.isRecording || !this.audioWorkletNode) {
            console.warn('⚠️ Cannot start recording: missing dependencies or already recording');
            return;
        }

        // Handle PCM data from AudioWorklet for both VAD and transcription
        this.audioWorkletNode.port.onmessage = (event) => {
            if (event.data.type === 'audioData' && this.socket && this.isConnected && this.isRecording) {
                this.sendPCMData(event.data.data);
            }
        };

        console.log('🎤 Recording started with PCM audio capture');
        this.isRecording = true;
    }

    stopRecording(): void {
        if (this.isRecording) {
            console.log('🎤 Recording stopped');
            this.isRecording = false;
        }
    }


    private sendPCMData(pcmData: Float32Array): void {
        try {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                // Send PCM data with a type identifier
                const message = {
                    type: 'pcm',
                    data: Array.from(pcmData),
                    sampleRate: 48000
                };
                this.socket.send(JSON.stringify(message));
                console.log(`🎵 PCM: Sent ${pcmData.length} samples for VAD and transcription`);
            }
        } catch (error) {
            console.error('❌ Error sending PCM data:', error);
        }
    }

    private handleTranscriptionResult(data: any): void {
        if (data.status === 'success') {
            console.log(`🎤 VAD Transcription: "${data.transcription}" (confidence: ${data.confidence})`);

            const event = new CustomEvent('transcription', {
                detail: {
                    text: data.transcription,
                    confidence: data.confidence,
                    languageCode: data.language_code
                }
            });
            window.dispatchEvent(event);
        } else if (data.status === 'error') {
            console.error('❌ Transcription error:', data.error);

            const event = new CustomEvent('transcription-error', {
                detail: {error: data.error}
            });
            window.dispatchEvent(event);
        }
    }

    disconnect(): void {
        this.stopRecording();

        // Clean up AudioContext resources
        if (this.audioWorkletNode) {
            this.audioWorkletNode.disconnect();
            this.audioWorkletNode = null;
        }

        if (this.sourceNode) {
            this.sourceNode.disconnect();
            this.sourceNode = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }

        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }

        this.isConnected = false;
    }

    isRecordingActive(): boolean {
        return this.isRecording;
    }

    isSocketConnected(): boolean {
        return this.isConnected;
    }
}