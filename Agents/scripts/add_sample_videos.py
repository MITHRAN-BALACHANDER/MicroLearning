"""
Add videos from data/videos folder to the database
Replaces all existing videos with fresh videos from the folder
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import init_db, get_db, add_video
from database.models import Video
from loguru import logger


def add_videos_from_folder():
    """Scan videos folder and add to database, removing old samples"""
    
    videos_dir = Path(__file__).parent.parent / "data" / "videos"
    
    if not videos_dir.exists():
        print(f"❌ Videos directory not found: {videos_dir}")
        print("Please create the directory and add video files.")
        return
    
    # Find all video files (case-insensitive, no duplicates)
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
    video_files = []
    seen = set()
    
    for ext in video_extensions:
        for file in videos_dir.glob(f"*{ext}"):
            if file.name.lower() not in seen:
                video_files.append(file)
                seen.add(file.name.lower())
    
    if not video_files:
        print(f"❌ No video files found in {videos_dir}")
        print(f"Supported formats: {', '.join(video_extensions)}")
        return
    
    print(f"📁 Found {len(video_files)} video file(s) in {videos_dir}\n")
    
    try:
        init_db()
        
        # Remove all existing videos (including samples)
        with get_db() as db:
            existing_count = db.query(Video).count()
            if existing_count > 0:
                print(f"�️  Removing {existing_count} existing video(s) from database...")
                db.query(Video).delete()
                db.commit()
                print("✅ Cleared old videos\n")
        
        added_count = 0
        
        for idx, video_path in enumerate(video_files, 1):
            print(f"📹 Processing ({idx}/{len(video_files)}): {video_path.name}")
            
            # Generate title from filename
            title = video_path.stem.replace('_', ' ').replace('-', ' ').title()
            
            # Use local file path as file_id (will need to be updated with Telegram file_id)
            file_id = f"LOCAL_{video_path.name}"
            
            # Generate description and concepts from filename
            description = f"Learning video: {title}"
            concepts = [word.lower() for word in title.split() if len(word) > 3][:5]
            
            try:
                # Add to database
                video = add_video(
                    title=title,
                    description=description,
                    file_id=file_id,
                    transcript=f"Video content from {video_path.name}. Transcript to be added.",
                    concepts=concepts if concepts else ["learning"],
                    difficulty_level=idx  # Simple progression
                )
                
                print(f"   ✅ Added: {title} (ID: {video.id})")
                print(f"   📋 Path: {video_path}")
                print(f"   🆔 File ID: {file_id}\n")
                added_count += 1
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}\n")
                logger.error(f"Error adding {video_path.name}: {str(e)}")
        
        print(f"{'='*60}")
        print(f"🎉 Successfully added {added_count}/{len(video_files)} video(s)!")
        print(f"{'='*60}\n")
        
        if added_count > 0:
            print("📝 Next Steps:")
            print("\n1. Get Telegram file_ids:")
            print("   a. Start your bot: python main.py")
            print("   b. Send each video to your bot")
            print("   c. Bot will reply with the file_id")
            print("   d. Copy the file_ids")
            
            print("\n2. Update database:")
            print("   python scripts/update_video_file_ids.py")
            
            print("\n📊 Current videos in database:")
            with get_db() as db:
                videos = db.query(Video).all()
                for v in videos:
                    print(f"   • {v.title}")
                    print(f"     File ID: {v.file_id}")
        
    except Exception as e:
        logger.error(f"Error in process: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def add_sample_videos():
    """Main entry point"""
    add_videos_from_folder()


if __name__ == "__main__":
    add_sample_videos()
