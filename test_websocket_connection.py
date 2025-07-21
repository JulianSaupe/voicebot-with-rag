#!/usr/bin/env python3
"""
Simple test script to verify WebSocket connection to the speech transcription endpoint.
"""

import asyncio
import websockets
import json

async def test_websocket_connection():
    """Test WebSocket connection to the speech transcription endpoint."""
    uri = "ws://localhost:8000/ws/speech"
    
    try:
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send a small test message (empty bytes to test connection)
            await websocket.send(b"")
            print("📤 Sent test data")
            
            # Wait briefly for any response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                result = json.loads(response)
                print(f"📝 Received response: {result}")
            except asyncio.TimeoutError:
                print("⏰ No immediate response (this is expected for empty data)")
            
            print("✅ WebSocket connection test completed successfully")
                
    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure the backend server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing WebSocket: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing WebSocket Connection")
    print("=" * 40)
    success = asyncio.run(test_websocket_connection())
    if success:
        print("🎉 WebSocket backend is working!")
    else:
        print("💥 WebSocket backend test failed!")