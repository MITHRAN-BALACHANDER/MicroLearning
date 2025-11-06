"""Check if Videos were created"""
from database.operations import SessionLocal
from database.models import Video, VideoGenerationJob

db = SessionLocal()

# Check the job
job = db.query(VideoGenerationJob).filter(
    VideoGenerationJob.task_id == '788e06ec66a1e8915d1ad4b5587ed317'
).first()

print("=" * 60)
print("VideoGenerationJob Status:")
print("=" * 60)
if job:
    print(f"Job ID: {job.id}")
    print(f"Status: {job.status}")
    print(f"Video URL: {job.video_url}")
    print(f"Prompt: {job.prompt[:80]}...")
else:
    print("Job not found!")

print()
print("=" * 60)
print("Video Table:")
print("=" * 60)

total_videos = db.query(Video).count()
print(f"Total Videos in Database: {total_videos}")
print()

videos = db.query(Video).order_by(Video.created_at.desc()).limit(5).all()
for v in videos:
    print(f"Video #{v.id}:")
    print(f"  Title: {v.title}")
    print(f"  file_id: {v.file_id[:80] if v.file_id and len(v.file_id) > 80 else v.file_id}")
    print(f"  Created: {v.created_at}")
    print()

db.close()

print("=" * 60)
if total_videos == 0:
    print("❌ No videos found!")
    print("The Video creation might have failed silently.")
else:
    print(f"✅ Found {total_videos} video(s) in database")
