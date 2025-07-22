// Test script to verify that all new services work correctly
import { WebSocketHandler } from './WebSocketHandler';
import { TextInputService } from './TextInputService';
import { MicrophoneInputService } from './MicrophoneInputService';
import { AudioPlaybackService } from './AudioPlaybackService';
import { ServiceManager } from './ServiceManager';

console.log('🧪 Testing service imports...');

// Test WebSocketHandler
try {
    const wsHandler = new WebSocketHandler('ws://localhost:8000/ws/speech');
    console.log('✅ WebSocketHandler imported and instantiated successfully');
} catch (error) {
    console.error('❌ WebSocketHandler test failed:', error);
}

// Test TextInputService
try {
    const wsHandler = new WebSocketHandler('ws://localhost:8000/ws/speech');
    const textService = new TextInputService(wsHandler);
    console.log('✅ TextInputService imported and instantiated successfully');
} catch (error) {
    console.error('❌ TextInputService test failed:', error);
}

// Test MicrophoneInputService
try {
    const wsHandler = new WebSocketHandler('ws://localhost:8000/ws/speech');
    const micService = new MicrophoneInputService(wsHandler);
    console.log('✅ MicrophoneInputService imported and instantiated successfully');
} catch (error) {
    console.error('❌ MicrophoneInputService test failed:', error);
}

// Test AudioPlaybackService
try {
    const audioService = new AudioPlaybackService();
    console.log('✅ AudioPlaybackService imported and instantiated successfully');
} catch (error) {
    console.error('❌ AudioPlaybackService test failed:', error);
}

// Test ServiceManager
try {
    const serviceManager = new ServiceManager({ 
        speechWsUrl: 'ws://localhost:8000/ws/speech',
        textWsUrl: 'ws://localhost:8000/ws/text'
    });
    console.log('✅ ServiceManager imported and instantiated successfully');
    
    // Test status getters
    console.log('📊 ServiceManager status:');
    console.log('  - Connected:', serviceManager.connected);
    console.log('  - Initialized:', serviceManager.initialized);
    console.log('  - Microphone Initialized:', serviceManager.microphoneInitialized);
    console.log('  - Recording:', serviceManager.recording);
    console.log('  - Audio Playing:', serviceManager.audioPlaying);
    
} catch (error) {
    console.error('❌ ServiceManager test failed:', error);
}

console.log('🧪 Service import tests completed!');

export { };