"""
Quick status check for video downloads and database
"""
import os
from pathlib import Path

# Paths
VIDEO_DIR = Path(__file__).parent.parent / "data" / "videos" / "uploads"
DB_PATH = Path(__file__).parent.parent / "data" / "microlearning.db"

print("\n" + "="*60)
print("VIDEO DOWNLOAD STATUS")
print("="*60)

# Check video directory
if VIDEO_DIR.exists():
    video_files = list(VIDEO_DIR.glob("*.mp4"))
    print(f"Video Directory: {VIDEO_DIR}")
    print(f"Total MP4 files: {len(video_files)}")
    
    if video_files:
        print("\nDownloaded Videos:")
        total_size = 0
        for i, video in enumerate(video_files, 1):
            size_mb = video.stat().st_size / (1024 * 1024)
            total_size += size_mb
            print(f"  {i}. {video.name} ({size_mb:.2f} MB)")
        print(f"\nTotal Size: {total_size:.2f} MB")
    else:
        print("No MP4 files found yet (download may be in progress)")
else:
    print(f"❌ Video directory not found: {VIDEO_DIR}")

# Check database
print("\n" + "="*60)
print("DATABASE STATUS")
print("="*60)

if DB_PATH.exists():
    size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    print(f"Database: {DB_PATH}")
    print(f"Size: {size_mb:.2f} MB")
    
    # Try to query database
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from database.operations import get_db
        from database.models import Video, Question
        
        with get_db() as db:
            videos = db.query(Video).all()
            videos_with_paths = db.query(Video).filter(Video.file_path != None).all()
            questions = db.query(Question).all()
            
            print(f"\nVideos in database: {len(videos)}")
            print(f"Videos with local file paths: {len(videos_with_paths)}")
            print(f"Questions generated: {len(questions)}")
            
            if videos_with_paths:
                print("\nVideos with downloaded files:")
                for i, video in enumerate(videos_with_paths[:10], 1):
                    print(f"  {i}. {video.title[:40]}... (Path: {video.file_path[:50]}...)")
                if len(videos_with_paths) > 10:
                    print(f"  ... and {len(videos_with_paths) - 10} more")
    except Exception as e:
        print(f"Could not query database: {str(e)}")
else:
    print(f"❌ Database not found: {DB_PATH}")

print("\n" + "="*60)
print("NEXT STEPS")
print("="*60)
print("1. Wait for all videos to download")
print("2. Run: python scripts/verify_sync.py")
print("3. Run: python main.py (start application)")
print("4. Visit: http://localhost:5000/videos")
print("="*60 + "\n")
