import { API_CONFIG } from './config';

/**
 * Speech recognition service for handling microphone input and transcription
 */

export interface SpeechState {
    isMicrophoneEnabled: boolean;
    isRecording: boolean;
    mediaRecorder: MediaRecorder | null;
}

export const createSpeechState = (): SpeechState => ({
    isMicrophoneEnabled: false,
    isRecording: false,
    mediaRecorder: null
});

/**
 * Toggle microphone access
 */
export const toggleMicrophone = async (
    speechState: SpeechState,
    updateCallback: (updates: Partial<SpeechState>) => void,
    subtitleCallback: (text: string) => void
): Promise<void> => {
    if (!speechState.isMicrophoneEnabled) {
        try {
            await navigator.mediaDevices.getUserMedia({ audio: true });
            updateCallback({ isMicrophoneEnabled: true });
            subtitleCallback('Microphone enabled. Click record to start speaking...');
        } catch (error) {
            console.error('Error accessing microphone:', error);
            subtitleCallback('Error: Could not access microphone');
        }
    } else {
        updateCallback({ isMicrophoneEnabled: false });
        if (speechState.isRecording) {
            await stopRecording(speechState, updateCallback, subtitleCallback);
        }
        subtitleCallback('Microphone disabled');
    }
};

/**
 * Start recording audio
 */
export const startRecording = async (
    speechState: SpeechState,
    updateCallback: (updates: Partial<SpeechState>) => void,
    subtitleCallback: (text: string) => void
): Promise<void> => {
    if (!speechState.isMicrophoneEnabled) return;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks: Blob[] = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await sendAudioToBackend(audioBlob, subtitleCallback);
            
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
        console.error('Error starting recording:', error);
        subtitleCallback('Error: Could not start recording');
    }
};

/**
 * Stop recording audio
 */
export const stopRecording = async (
    speechState: SpeechState,
    updateCallback: (updates: Partial<SpeechState>) => void,
    subtitleCallback: (text: string) => void
): Promise<void> => {
    if (speechState.mediaRecorder && speechState.isRecording) {
        speechState.mediaRecorder.stop();
        updateCallback({ 
            isRecording: false,
            mediaRecorder: null
        });
        subtitleCallback('Processing audio...');
    }
};

/**
 * Send audio to backend for transcription
 */
const sendAudioToBackend = async (
    audioBlob: Blob,
    subtitleCallback: (text: string) => void
): Promise<string | null> => {
    try {
        const response = await fetch(API_CONFIG.getSpeechUrl(), {
            method: 'POST',
            body: audioBlob,
            headers: {
                'Content-Type': 'audio/webm'
            }
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Transcription result:', result);
            if (result.transcription) {
                subtitleCallback(`Transcribed: "${result.transcription}"`);
                return result.transcription;
            } else {
                subtitleCallback('No speech detected');
                return null;
            }
        } else {
            console.error('Error sending audio to backend:', response.statusText);
            subtitleCallback('Error: Could not process audio');
            return null;
        }
    } catch (error) {
        console.error('Error sending audio to backend:', error);
        subtitleCallback('Error: Could not connect to server');
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
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks: Blob[] = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
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