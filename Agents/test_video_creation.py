"""
Test callback with real data to verify Video creation
"""
import requests
import json

# Use one of your real task IDs
task_id = "788e06ec66a1e8915d1ad4b5587ed317"  # Your Job #1

callback_data = {
    "code": 200,
    "data": {
        "state": "success",
        "taskId": task_id,
        "resultJson": json.dumps({
            "resultUrls": ["https://example.com/test-generated-video.mp4"]
        })
    }
}

print("=" * 60)
print("Testing Callback with Real Task ID")
print("=" * 60)
print(f"Task ID: {task_id}")
print()

try:
    response = requests.post(
        "http://localhost:5000/api/kie_callback",
        json=callback_data,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    if response.status_code == 200:
        print("✅ Callback processed successfully!")
        print()
        print("Now check your database:")
        print("1. VideoGenerationJob should be marked as 'completed'")
        print("2. A new Video entry should be created")
        print()
        print("Run this to check:")
        print("""
from database.operations import SessionLocal
from database.models import Video, VideoGenerationJob

db = SessionLocal()
job = db.query(VideoGenerationJob).filter(VideoGenerationJob.task_id == '788e06ec66a1e8915d1ad4b5587ed317').first()
print(f"Job Status: {job.status}")
print(f"Job Video URL: {job.video_url}")

videos = db.query(Video).order_by(Video.created_at.desc()).limit(3).all()
for v in videos:
    print(f"Video #{v.id}: {v.title} - {v.file_id}")
db.close()
        """)
    else:
        print(f"❌ Error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Connection Error: {e}")
    print()
    print("Make sure Flask server is running on port 5000")
