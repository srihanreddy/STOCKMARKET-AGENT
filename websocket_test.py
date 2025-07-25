import asyncio
import websockets
import json
import sys

async def test_websocket():
    """Test WebSocket functionality"""
    uri = "wss://3030ffac-5aab-46d6-8951-e2c8807dde4b.preview.emergentagent.com/ws/test_client"
    
    try:
        print("🔌 Testing WebSocket connection...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Send stock subscription message
            message = {
                "type": "stock_subscribe",
                "symbol": "AAPL"
            }
            
            await websocket.send(json.dumps(message))
            print("✅ Sent stock subscription message")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                data = json.loads(response)
                
                print(f"✅ Received WebSocket response:")
                print(f"   Type: {data.get('type', 'N/A')}")
                print(f"   Symbol: {data.get('symbol', 'N/A')}")
                print(f"   Price: ${data.get('price', 'N/A')}")
                print(f"   Volume: {data.get('volume', 'N/A'):,}")
                print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
                
                return True
                
            except asyncio.TimeoutError:
                print("⚠️  WebSocket response timeout (30s)")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {str(e)}")
        return False

async def main():
    print("🚀 Starting WebSocket Tests")
    print("=" * 50)
    
    success = await test_websocket()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 WebSocket test passed!")
        return 0
    else:
        print("⚠️  WebSocket test failed or timed out")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))