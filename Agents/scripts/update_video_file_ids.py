"""
Helper script to update video file_ids in the database
After uploading videos to Telegram, use this to update the database with real file_ids
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import get_db
from database.models import Video
from loguru import logger


def update_file_ids():
    """Interactive script to update video file_ids"""
    
    print("="*60)
    print("Video File ID Updater")
    print("="*60)
    print()
    
    with get_db() as db:
        videos = db.query(Video).all()
        
        if not videos:
            print("❌ No videos found in database.")
            print("   Run: python scripts/add_sample_videos.py")
            return
        
        print(f"Found {len(videos)} video(s) in database:\n")
        
        for idx, video in enumerate(videos, 1):
            needs_update = video.file_id.startswith("LOCAL_") or video.file_id.startswith("SAMPLE_")
            status = "⚠️  NEEDS UPDATE" if needs_update else "✅ OK"
            
            print(f"{idx}. {status}")
            print(f"   Title: {video.title}")
            print(f"   Current file_id: {video.file_id}")
            print()
        
        print("-"*60)
        print("\nHow to get Telegram file_ids:")
        print("1. Start your bot: python main.py")
        print("2. Send a video to your bot")
        print("3. Check the bot logs for the file_id")
        print("4. The file_id looks like: BAACAgIAAxkBAAIC...")
        print()
        print("Or use @getidsbot in Telegram:")
        print("1. Forward your video to @getidsbot")
        print("2. Bot will reply with the file_id")
        print()
        print("-"*60)
        print()
        
        # Interactive update
        while True:
            choice = input("Enter video number to update (or 'q' to quit): ").strip()
            
            if choice.lower() == 'q':
                break
            
            try:
                idx = int(choice)
                if idx < 1 or idx > len(videos):
                    print(f"❌ Invalid number. Please enter 1-{len(videos)}")
                    continue
                
                video = videos[idx - 1]
                print(f"\nUpdating: {video.title}")
                print(f"Current file_id: {video.file_id}")
                
                new_file_id = input("Enter new file_id (or 'skip'): ").strip()
                
                if new_file_id.lower() == 'skip':
                    print("Skipped.\n")
                    continue
                
                if len(new_file_id) < 20:
                    print("❌ File ID seems too short. Telegram file_ids are usually 50+ characters.")
                    retry = input("Use anyway? (y/n): ").strip().lower()
                    if retry != 'y':
                        continue
                
                # Update in database
                video.file_id = new_file_id
                db.commit()
                
                print(f"✅ Updated successfully!")
                print(f"   New file_id: {new_file_id}\n")
                
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit\n")
            except Exception as e:
                print(f"❌ Error: {str(e)}\n")
        
        print("\n" + "="*60)
        print("Final Status:")
        print("="*60)
        
        with get_db() as db:
            videos = db.query(Video).all()
            ready_count = 0
            
            for video in videos:
                needs_update = video.file_id.startswith("LOCAL_") or video.file_id.startswith("SAMPLE_")
                status = "⚠️  NEEDS UPDATE" if needs_update else "✅ READY"
                
                if not needs_update:
                    ready_count += 1
                
                print(f"{status} - {video.title}")
            
            print()
            print(f"  Summary: {ready_count}/{len(videos)} videos ready")
            
            if ready_count == len(videos):
                print("🎉 All videos have valid file_ids! You can now use the bot.")
            else:
                print("⚠️  Some videos still need file_ids. Update them to enable video delivery.")


if __name__ == "__main__":
    update_file_ids()
