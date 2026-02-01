"""
Script to reset videos database:
1. Remove all existing videos from the database
2. Scan videos folder and add all video files as new entries
"""
import os
import sys
from pathlib import Path
from typing import List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import get_db
from database.models import Video, Question, VideoProgress
from config.settings import VIDEOS_DIR


class VideoResetManager:
    """Manage resetting videos in database from folder"""
    
    def __init__(self):
        self.videos_dir = Path(VIDEOS_DIR)
        logger.info(f"Videos directory: {self.videos_dir}")
    
    def find_all_video_files(self) -> List[Path]:
        """Find all video files in the videos directory"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.mp3', '.wav']
        video_files = []
        
        logger.info(f"Scanning for videos in: {self.videos_dir}")
        
        # Search in all subdirectories
        for ext in video_extensions:
            found = list(self.videos_dir.rglob(f"*{ext}"))
            video_files.extend(found)
            if found:
                logger.info(f"  Found {len(found)} {ext} files")
        
        logger.info(f"Total video files found: {len(video_files)}")
        return video_files
    
    def delete_all_videos(self):
        """Delete all videos and related data from database"""
        logger.info("Deleting all existing videos and related data...")
        
        with get_db() as db:
            # Delete related data first
            questions_deleted = db.query(Question).delete()
            progress_deleted = db.query(VideoProgress).delete()
            videos_deleted = db.query(Video).delete()
            
            db.commit()
            
            logger.info(f"✅ Deleted {videos_deleted} videos")
            logger.info(f"✅ Deleted {questions_deleted} questions")
            logger.info(f"✅ Deleted {progress_deleted} progress records")
    
    def add_video_to_db(self, video_path: Path, order_index: int) -> Video:
        """Add a single video to the database"""
        with get_db() as db:
            # Generate title from filename
            filename = video_path.stem
            title = filename.replace('_', ' ').replace('-', ' ').title()
            
            # Determine category from path or filename
            category = 'general'
            path_str = str(video_path).lower()
            if 'technical' in path_str or 'tech' in path_str:
                category = 'technical'
            elif 'business' in path_str:
                category = 'business'
            elif 'onboarding' in path_str:
                category = 'onboarding'
            
            # Get file size
            file_size = video_path.stat().st_size
            
            # Create video entry
            video = Video(
                title=title,
                description=f"Video: {filename}",
                file_id=str(video_path),  # Use full path as file_id
                file_path=str(video_path),
                category=category,
                difficulty_level=1,  # Default difficulty
                order_index=order_index,
                is_active=True
            )
            
            db.add(video)
            db.commit()
            db.refresh(video)
            
            logger.info(f"  Added: {title} ({file_size / (1024*1024):.2f} MB)")
            return video
    
    def add_all_videos_from_folder(self):
        """Add all videos from folder to database"""
        logger.info("\nAdding all videos from folder to database...")
        
        video_files = self.find_all_video_files()
        
        if not video_files:
            logger.warning("No video files found in the videos directory!")
            return
        
        logger.info(f"\nAdding {len(video_files)} videos to database...")
        logger.info("-" * 70)
        
        added_count = 0
        error_count = 0
        
        for idx, video_path in enumerate(sorted(video_files), 1):
            try:
                self.add_video_to_db(video_path, order_index=idx)
                added_count += 1
            except Exception as e:
                logger.error(f"❌ Error adding video {video_path.name}: {str(e)}")
                error_count += 1
        
        logger.info("-" * 70)
        logger.info(f"✅ Successfully added {added_count} videos")
        if error_count > 0:
            logger.warning(f"⚠️  Failed to add {error_count} videos")
    
    def reset_videos(self):
        """Main function to reset all videos"""
        logger.info("="*70)
        logger.info("RESETTING VIDEOS DATABASE")
        logger.info("="*70)
        
        # Step 1: Delete all existing videos
        self.delete_all_videos()
        
        # Step 2: Add all videos from folder
        self.add_all_videos_from_folder()
        
        # Print summary
        with get_db() as db:
            total_videos = db.query(Video).count()
            
        logger.info("\n" + "="*70)
        logger.info("VIDEO RESET COMPLETE")
        logger.info("="*70)
        logger.info(f"Total videos in database: {total_videos}")
        logger.info("="*70)
        logger.info("\nNext steps:")
        logger.info("  1. Use the video analysis script to generate questions")
        logger.info("  2. Or manually add questions using the admin dashboard")
        logger.info("="*70)


def main():
    """Main entry point"""
    logger.info("Starting video database reset...")
    logger.info("This will:")
    logger.info("  1. DELETE ALL existing videos, questions, and progress")
    logger.info("  2. ADD ALL videos found in the videos folder")
    logger.info("")
    
    import time
    logger.info("Starting in 3 seconds... (Press Ctrl+C to cancel)")
    time.sleep(3)
    
    manager = VideoResetManager()
    manager.reset_videos()
    
    logger.info("\nVideo reset completed!")


if __name__ == "__main__":
    main()
