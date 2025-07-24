#!/usr/bin/env python3
"""
Test script to verify WebSocket-based cancellation functionality.
This script tests the complete workflow from process creation to cancellation.
"""

import asyncio
import json
import numpy as np
import websockets
import time
from typing import List, Dict, Any


class TranscriptionCancellationTester:
    """Test class for verifying transcription cancellation functionality."""
    
    def __init__(self, websocket_url: str = "ws://localhost:8000/ws/speech"):
        self.websocket_url = websocket_url
        self.websocket = None
        self.received_messages: List[Dict[str, Any]] = []
        self.current_process_id = None
        
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            print(f"✅ Connected to {self.websocket_url}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected from WebSocket")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the WebSocket server."""
        if not self.websocket:
            raise RuntimeError("WebSocket not connected")
        
        await self.websocket.send(json.dumps(message))
        print(f"📤 Sent: {message['type']}")
    
    async def receive_messages(self, timeout: float = 5.0):
        """Receive messages from WebSocket with timeout."""
        messages = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                try:
                    # Set a short timeout for each receive attempt
                    message = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=0.5
                    )
                    
                    data = json.loads(message)
                    messages.append(data)
                    self.received_messages.append(data)
                    
                    print(f"📥 Received: {data['type']}")
                    
                    # Update current process ID if we get a transcription_started event
                    if data['type'] == 'transcription_started':
                        self.current_process_id = data.get('process_id')
                        print(f"🆔 Process ID: {self.current_process_id}")
                    
                    # Stop receiving if we get a completion/cancellation event
                    if data['type'] in ['transcription_completed', 'transcription_cancelled', 
                                       'transcription_stopped', 'transcription_error']:
                        break
                        
                except asyncio.TimeoutError:
                    continue
                    
        except Exception as e:
            print(f"❌ Error receiving messages: {e}")
        
        return messages
    
    def generate_test_audio_data(self, duration_seconds: float = 2.0, sample_rate: int = 48000) -> List[float]:
        """Generate test audio data (sine wave)."""
        samples = int(duration_seconds * sample_rate)
        t = np.linspace(0, duration_seconds, samples)
        # Generate a 440Hz sine wave (A note)
        frequency = 440.0
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
        return audio_data.tolist()
    
    async def test_start_transcription(self):
        """Test starting a transcription process."""
        print("\n🧪 Testing start transcription...")
        
        audio_data = self.generate_test_audio_data(duration_seconds=3.0)
        
        message = {
            "type": "start_transcription",
            "audio_data": audio_data,
            "language_code": "de-DE",
            "metadata": {
                "test": "cancellation_test",
                "timestamp": time.time()
            }
        }
        
        await self.send_message(message)
        
        # Wait for response
        messages = await self.receive_messages(timeout=10.0)
        
        # Check if we got a transcription_started event
        started_events = [msg for msg in messages if msg['type'] == 'transcription_started']
        if started_events:
            print("✅ Transcription started successfully")
            return True
        else:
            print("❌ Failed to start transcription")
            return False
    
    async def test_stop_transcription(self):
        """Test stopping a transcription process."""
        print("\n🧪 Testing stop transcription...")
        
        if not self.current_process_id:
            print("❌ No active process to stop")
            return False
        
        message = {
            "type": "stop_transcription",
            "process_id": self.current_process_id,
            "reason": "Test cancellation"
        }
        
        await self.send_message(message)
        
        # Wait for response
        messages = await self.receive_messages(timeout=5.0)
        
        # Check if we got a transcription_stopped or transcription_cancelled event
        stop_events = [msg for msg in messages if msg['type'] in ['transcription_stopped', 'transcription_cancelled']]
        if stop_events:
            print("✅ Transcription stopped successfully")
            return True
        else:
            print("❌ Failed to stop transcription")
            return False
    
    async def test_stop_all_transcriptions(self):
        """Test stopping all transcription processes."""
        print("\n🧪 Testing stop all transcriptions...")
        
        message = {
            "type": "stop_all_transcriptions",
            "reason": "Test stop all"
        }
        
        await self.send_message(message)
        
        # Wait for response
        messages = await self.receive_messages(timeout=5.0)
        
        # Check if we got an all_transcriptions_stopped event
        stop_all_events = [msg for msg in messages if msg['type'] == 'all_transcriptions_stopped']
        if stop_all_events:
            print("✅ All transcriptions stopped successfully")
            return True
        else:
            print("❌ Failed to stop all transcriptions")
            return False
    
    async def test_cancellation_during_processing(self):
        """Test cancelling a transcription while it's processing."""
        print("\n🧪 Testing cancellation during processing...")
        
        # Start a transcription with longer audio
        audio_data = self.generate_test_audio_data(duration_seconds=10.0)  # Longer audio
        
        start_message = {
            "type": "start_transcription",
            "audio_data": audio_data,
            "language_code": "de-DE",
            "metadata": {"test": "cancellation_during_processing"}
        }
        
        await self.send_message(start_message)
        
        # Wait a bit for the process to start
        await asyncio.sleep(1.0)
        
        # Receive initial messages
        initial_messages = await self.receive_messages(timeout=2.0)
        
        # Check if transcription started
        started_events = [msg for msg in initial_messages if msg['type'] == 'transcription_started']
        if not started_events:
            print("❌ Transcription didn't start")
            return False
        
        # Now cancel it while it's processing
        stop_message = {
            "type": "stop_transcription",
            "process_id": self.current_process_id,
            "reason": "Cancelled during processing test"
        }
        
        await self.send_message(stop_message)
        
        # Wait for cancellation response
        cancellation_messages = await self.receive_messages(timeout=5.0)
        
        # Check if we got a cancellation event
        cancel_events = [msg for msg in cancellation_messages 
                        if msg['type'] in ['transcription_cancelled', 'transcription_stopped']]
        if cancel_events:
            print("✅ Successfully cancelled transcription during processing")
            return True
        else:
            print("❌ Failed to cancel transcription during processing")
            return False
    
    async def test_pcm_data_compatibility(self):
        """Test that existing PCM data functionality still works."""
        print("\n🧪 Testing PCM data compatibility...")
        
        # Generate small PCM chunks
        chunk_size = 1024
        audio_data = self.generate_test_audio_data(duration_seconds=1.0)
        
        # Send PCM data in chunks
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            
            pcm_message = {
                "type": "pcm",
                "data": chunk
            }
            
            await self.send_message(pcm_message)
            await asyncio.sleep(0.1)  # Small delay between chunks
        
        # Wait for transcription results
        messages = await self.receive_messages(timeout=10.0)
        
        # Check if we got transcription results
        transcription_events = [msg for msg in messages if msg['type'] == 'transcription']
        if transcription_events:
            print("✅ PCM data compatibility maintained")
            return True
        else:
            print("❌ PCM data compatibility broken")
            return False
    
    def print_test_summary(self):
        """Print a summary of all received messages."""
        print("\n📊 Test Summary:")
        print(f"Total messages received: {len(self.received_messages)}")
        
        message_types = {}
        for msg in self.received_messages:
            msg_type = msg.get('type', 'unknown')
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        for msg_type, count in message_types.items():
            print(f"  {msg_type}: {count}")
    
    async def run_all_tests(self):
        """Run all cancellation tests."""
        print("🚀 Starting WebSocket Cancellation Functionality Tests")
        print("=" * 60)
        
        # Connect to WebSocket
        if not await self.connect():
            return False
        
        try:
            test_results = []
            
            # Test 1: Basic start transcription
            result1 = await self.test_start_transcription()
            test_results.append(("Start Transcription", result1))
            
            # Test 2: Stop transcription
            result2 = await self.test_stop_transcription()
            test_results.append(("Stop Transcription", result2))
            
            # Test 3: Stop all transcriptions
            result3 = await self.test_stop_all_transcriptions()
            test_results.append(("Stop All Transcriptions", result3))
            
            # Test 4: Cancellation during processing
            result4 = await self.test_cancellation_during_processing()
            test_results.append(("Cancellation During Processing", result4))
            
            # Test 5: PCM data compatibility
            result5 = await self.test_pcm_data_compatibility()
            test_results.append(("PCM Data Compatibility", result5))
            
            # Print results
            print("\n" + "=" * 60)
            print("🏁 Test Results:")
            
            passed = 0
            for test_name, result in test_results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {test_name}: {status}")
                if result:
                    passed += 1
            
            print(f"\nOverall: {passed}/{len(test_results)} tests passed")
            
            # Print message summary
            self.print_test_summary()
            
            return passed == len(test_results)
            
        finally:
            await self.disconnect()


async def main():
    """Main test function."""
    tester = TranscriptionCancellationTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 All tests passed! Cancellation functionality is working correctly.")
            return 0
        else:
            print("\n💥 Some tests failed. Please check the implementation.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    
    print("WebSocket Transcription Cancellation Test Suite")
    print("Make sure the backend server is running on localhost:8000")
    print("Press Ctrl+C to interrupt tests\n")
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)