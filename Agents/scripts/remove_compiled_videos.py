"""
Remove all videos with 'compiled' in the name from database
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.models import Video, Question, VideoProgress, Base
from config.settings import DATABASE_URL

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def remove_compiled_videos():
    """Remove all videos with 'compiled' in the name"""
    db = SessionLocal()
    try:
        # Find videos with 'compiled' in title
        compiled_videos = db.query(Video).filter(
            Video.title.ilike('%compiled%')
        ).all()
        
        if not compiled_videos:
            print("No videos with 'compiled' in the name found.")
            return
        
        print(f"Found {len(compiled_videos)} video(s) with 'compiled' in the name:")
        for video in compiled_videos:
            print(f"  - ID: {video.id}, Title: {video.title}")
        
        confirm = input("\nDelete these videos? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            return
        
        # Delete associated data first
        for video in compiled_videos:
            # Delete questions
            questions_deleted = db.query(Question).filter(
                Question.video_id == video.id
            ).delete()
            
            # Delete video progress
            progress_deleted = db.query(VideoProgress).filter(
                VideoProgress.video_id == video.id
            ).delete()
            
            print(f"Video {video.id}: Deleted {questions_deleted} questions, {progress_deleted} progress records")
        
        # Delete videos
        videos_deleted = db.query(Video).filter(
            Video.title.ilike('%compiled%')
        ).delete()
        
        db.commit()
        print(f"\n✓ Successfully deleted {videos_deleted} video(s) with 'compiled' in the name.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    remove_compiled_videos()
