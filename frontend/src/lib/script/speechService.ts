import {API_CONFIG} from './config';

/**
 * Speech recognition service for handling microphone input and transcription
 */

export interface SpeechState {
    isMicrophoneEnabled: boolean;
    isRecording: boolean;
    mediaRecorder: MediaRecorder | null;
    mediaStream: MediaStream | null;
    isStreaming: boolean;
}

export const createSpeechState = (): SpeechState => ({
    isMicrophoneEnabled: false,
    isRecording: false,
    mediaRecorder: null,
    mediaStream: null,
    isStreaming: false
});

export const toggleMicrophone = async (
    speechState: SpeechState,
    updateCallback: (updates: Partial<SpeechState>) => void,
    subtitleCallback: (text: string) => void,
    transcriptionCallback?: (text: string) => void
): Promise<void> => {
    if (!speechState.isMicrophoneEnabled) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 48000,  // Match backend expectation
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            updateCallback({
                isMicrophoneEnabled: true,
                mediaStream: stream
            });
            subtitleCallback('Microphone enabled. Starting continuous streaming...');

            // Start continuous streaming
            await startContinuousStreaming(speechState, updateCallback, subtitleCallback, transcriptionCallback);
        } catch (error) {
            console.error('Error accessing microphone:', error);
            subtitleCallback('Error: Could not access microphone');
        }
    } else {
        // Stop continuous streaming
        await stopContinuousStreaming(speechState, updateCallback, subtitleCallback);
        updateCallback({isMicrophoneEnabled: false});
        subtitleCallback('Microphone disabled');
    }
};

export const startContinuousStreaming = async (
    speechState: SpeechState,
    updateCallback: (updates: Partial<SpeechState>) => void,
    subtitleCallback: (text: string) => void,
    transcriptionCallback?: (text: string) => void
): Promise<void> => {
    if (!speechState.mediaStream) return;

    try {
        // Create WebSocket connection for transcription
        const websocket = await createTranscriptionWebSocket(subtitleCallback, transcriptionCallback);
        
        const mediaRecorder = new MediaRecorder(speechState.mediaStream, {
            mimeType: 'audio/webm;codecs=opus',
            audioBitsPerSecond: 48000  // Higher bitrate for better quality
        });

        let streamingInterval: number;

        mediaRecorder.ondataavailable = async (event) => {
            if (event.data.size > 0) {
                // Send audio chunk for transcription via WebSocket
                const audioBlob = new Blob([event.data], {type: 'audio/webm'});
                await sendAudioChunkForTranscription(audioBlob, subtitleCallback, transcriptionCallback, websocket);
            }
        };

        mediaRecorder.onstop = () => {
            if (streamingInterval) {
                clearInterval(streamingInterval);
            }
            // Close WebSocket connection when recording stops
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.close();
            }
        };

        // Start recording and request data every 2 seconds for continuous streaming
        mediaRecorder.start();
        streamingInterval = setInterval(() => {
            if (mediaRecorder.state === 'recording') {
                mediaRecorder.requestData();
            }
        }, 3000); // Increased to 3 seconds for better chunks

        updateCallback({
            isStreaming: true,
            mediaRecorder: mediaRecorder
        });

        subtitleCallback('Streaming audio... Speak now');
    } catch (error) {
        console.error('Error starting continuous streaming:', error);
        subtitleCallback('Error: Could not start audio streaming');
    }
};

/**
 * Stop continuous audio streaming
 */
export const stopContinuousStreaming = async (
    speechState: SpeechState,
    updateCallback: (updates: Partial<SpeechState>) => void,
    subtitleCallback: (text: string) => void
): Promise<void> => {
    if (speechState.mediaRecorder && speechState.isStreaming) {
        speechState.mediaRecorder.stop();
    }

    if (speechState.mediaStream) {
        speechState.mediaStream.getTracks().forEach(track => track.stop());
    }

    updateCallback({
        isStreaming: false,
        mediaRecorder: null,
        mediaStream: null
    });

    subtitleCallback('Audio streaming stopped');
};

/**
 * Send audio chunk for transcription via WebSocket
 */
const sendAudioChunkForTranscription = async (
    audioBlob: Blob,
    subtitleCallback: (text: string) => void,
    transcriptionCallback?: (text: string) => void,
    websocket?: WebSocket
): Promise<void> => {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        console.error('WebSocket not available for audio chunk transcription');
        return;
    }

    try {
        // Convert blob to array buffer and send via WebSocket
        const arrayBuffer = await audioBlob.arrayBuffer();
        websocket.send(arrayBuffer);
        console.log('Sent audio chunk via WebSocket:', arrayBuffer.byteLength, 'bytes');
    } catch (error) {
        console.error('Error sending audio chunk via WebSocket:', error);
    }
};

/**
 * Create WebSocket connection for audio transcription
 */
const createTranscriptionWebSocket = (
    subtitleCallback: (text: string) => void,
    transcriptionCallback?: (text: string) => void
): Promise<WebSocket> => {
    return new Promise((resolve, reject) => {
        const websocket = new WebSocket(API_CONFIG.getSpeechWebSocketUrl());
        
        websocket.onopen = () => {
            console.log('🔌 WebSocket connected for transcription');
            subtitleCallback('Connected to transcription service');
            resolve(websocket);
        };
        
        websocket.onmessage = (event) => {
            try {
                const result = JSON.parse(event.data);
                console.log('Transcription result:', result);
                
                if (result.status === 'success' && result.transcription) {
                    subtitleCallback(`Transcribed: "${result.transcription}"`);
                    if (transcriptionCallback) {
                        transcriptionCallback(result.transcription);
                    }
                } else if (result.status === 'error') {
                    console.error('Transcription error:', result.error);
                    subtitleCallback('Error: Could not process audio');
                }
            } catch (error) {
                console.error('Error parsing transcription result:', error);
            }
        };
        
        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            subtitleCallback('Error: Could not connect to transcription service');
            reject(error);
        };
        
        websocket.onclose = () => {
            console.log('🔌 WebSocket disconnected');
            subtitleCallback('Disconnected from transcription service');
        };
    });
};

/**
 * Send audio to backend for transcription via WebSocket
 */
const sendAudioToBackend = async (
    audioBlob: Blob,
    subtitleCallback: (text: string) => void
): Promise<string | null> => {
    try {
        const websocket = await createTranscriptionWebSocket(subtitleCallback);
        
        return new Promise((resolve) => {
            let transcriptionResult: string | null = null;
            
            // Set up message handler to capture transcription result
            const originalOnMessage = websocket.onmessage;
            websocket.onmessage = (event) => {
                try {
                    const result = JSON.parse(event.data);
                    if (result.status === 'success' && result.transcription) {
                        transcriptionResult = result.transcription;
                        subtitleCallback(`Transcribed: "${result.transcription}"`);
                        
                        // Close connection and resolve
                        websocket.close();
                        resolve(transcriptionResult);
                    } else if (result.status === 'error') {
                        console.error('Transcription error:', result.error);
                        subtitleCallback('Error: Could not process audio');
                        websocket.close();
                        resolve(null);
                    }
                } catch (error) {
                    console.error('Error parsing transcription result:', error);
                    websocket.close();
                    resolve(null);
                }
            };
            
            // Send audio data
            audioBlob.arrayBuffer().then(arrayBuffer => {
                websocket.send(arrayBuffer);
                console.log('Sent audio via WebSocket:', arrayBuffer.byteLength, 'bytes');
            });
            
            // Set timeout to avoid hanging
            setTimeout(() => {
                if (websocket.readyState === WebSocket.OPEN) {
                    websocket.close();
                }
                if (transcriptionResult === null) {
                    subtitleCallback('Timeout: No transcription received');
                    resolve(null);
                }
            }, 10000); // 10 second timeout
        });
        
    } catch (error) {
        console.error('Error in WebSocket transcription:', error);
        subtitleCallback('Error: Could not connect to transcription service');
        return null;
    }
};

/**
 * Complete speech recognition flow: record and transcribe
 */
export const recordAndTranscribe = async (
    speechState: SpeechState,
    updateCallback: (updates: Partial<SpeechState>) => void,
    subtitleCallback: (text: string) => void,
    transcriptionCallback: (text: string) => void
): Promise<void> => {
    if (!speechState.isMicrophoneEnabled) return;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({audio: true});
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks: Blob[] = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, {type: 'audio/webm'});
            const transcription = await sendAudioToBackend(audioBlob, subtitleCallback);

            if (transcription) {
                transcriptionCallback(transcription);
            }

            // Stop all tracks to release microphone
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        updateCallback({
            isRecording: true,
            mediaRecorder: mediaRecorder
        });
        subtitleCallback('Recording... Click stop when finished speaking');
    } catch (error) {
        console.error('Error in record and transcribe:', error);
        subtitleCallback('Error: Could not start recording');
    }
};