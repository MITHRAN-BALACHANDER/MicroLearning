"""
Test script to check Gemini File API response format
"""
import os
import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import GEMINI_API_KEY, VIDEOS_DIR

# Get first video file
videos_dir = Path(VIDEOS_DIR)
video_files = list(videos_dir.rglob("*.mp4"))

if not video_files:
    print("No video files found")
    sys.exit(1)

video_path = video_files[0]
print(f"Testing with: {video_path.name}")
print(f"File size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")

# Test upload
base_url = "https://generativelanguage.googleapis.com/v1beta"
upload_url = f"{base_url}/files?key={GEMINI_API_KEY}"

print(f"\nUploading to: {upload_url[:80]}...")

with open(video_path, 'rb') as f:
    files = {
        'file': (video_path.name, f, 'video/mp4')
    }
    headers = {
        'X-Goog-Upload-Protocol': 'multipart'
    }
    
    response = requests.post(upload_url, files=files, headers=headers)

print(f"\nStatus Code: {response.status_code}")
print(f"\nResponse Headers:")
for key, value in response.headers.items():
    print(f"  {key}: {value}")

print(f"\nResponse Body:")
print(response.text)

if response.status_code == 200:
    try:
        data = response.json()
        print(f"\nParsed JSON:")
        import json
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error parsing JSON: {e}")
