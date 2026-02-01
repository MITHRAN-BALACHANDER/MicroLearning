"""
Quick file_id updater - Paste file_id directly
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import get_db
from database.models import Video


def quick_update():
    """Quick update for single video"""
    
    print("="*60)
    print("Quick File ID Update")
    print("="*60)
    print()
    
    with get_db() as db:
        videos = db.query(Video).all()
        
        if not videos:
            print("❌ No videos in database")
            return
        
        print("Current videos:")
        for v in videos:
            print(f"  {v.id}. {v.title}")
            print(f"     Current file_id: {v.file_id}\n")
        
        print("="*60)
        print()
        print("  How to get file_id:")
        print("1. Open Telegram")
        print("2. Search for @getidsbot")
        print("3. Send your video to @getidsbot")
        print("4. Bot will reply with the file_id")
        print("5. Copy and paste it below")
        print()
        print("="*60)
        print()
        
        video_id = input("Enter video ID to update (or 'q' to quit): ").strip()
        
        if video_id.lower() == 'q':
            return
        
        try:
            vid = int(video_id)
            video = db.query(Video).filter(Video.id == vid).first()
            
            if not video:
                print(f"❌ Video {vid} not found")
                return
            
            print(f"\nUpdating: {video.title}")
            print(f"Current file_id: {video.file_id}\n")
            
            new_file_id = input("Paste the new file_id: ").strip()
            
            if len(new_file_id) < 20:
                print("⚠️  Warning: File ID seems too short")
                confirm = input("Continue anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Cancelled")
                    return
            
            # Update
            video.file_id = new_file_id
            db.commit()
            
            print(f"\n✅ Updated successfully!")
            print(f"   Video: {video.title}")
            print(f"   New file_id: {new_file_id}")
            print()
            print("🎉 You can now use /video in your bot!")
            
        except ValueError:
            print("❌ Invalid ID")
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    quick_update()
