"""
Test the KIE.AI callback endpoint
"""
import requests
import json

# Test data matching KIE.AI callback format
callback_data = {
    "code": 200,
    "data": {
        "state": "success",
        "taskId": "test-task-123",
        "resultJson": json.dumps({
            "resultUrls": ["https://example.com/test-video.mp4"]
        })
    }
}

print("=" * 60)
print("Testing KIE.AI Callback Endpoint")
print("=" * 60)
print()

# Test localhost
print("1. Testing localhost endpoint...")
try:
    response = requests.post(
        "http://localhost:5000/api/kie_callback",
        json=callback_data,
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✅ Localhost works!")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test ngrok URL
print("2. Testing ngrok public endpoint...")
ngrok_url = "https://unameliorable-andra-undetectably.ngrok-free.dev/api/kie_callback"
try:
    response = requests.post(
        ngrok_url,
        json=callback_data,
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")
    print("   ✅ ngrok endpoint works!")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 60)
print("If both tests pass, you're ready to generate videos!")
print("KIE.AI will automatically call your callback when done.")
print("=" * 60)
