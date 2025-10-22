#!/usr/bin/env python3
"""Direct database update for video file_id"""

from database.operations import SessionLocal
from database.models import Video

# The correct video file_id from the JSON
CORRECT_FILE_ID = "BAACAgUAAxkBAAEYkKNo-HHjoy8w1dgnhlZ9VNsR-2FQfAACpxgAAiIGyFeB48pUoTaIxzYE"

def update_file_id():
    db = SessionLocal()
    try:
        # Get the first video (ID = 1)
        video = db.query(Video).filter(Video.id == 1).first()
        
        if not video:
            print("❌ No video found with ID 1")
            return
        
        print(f"Current video: {video.title}")
        print(f"Old file_id: {video.file_id}")
        print(f"Old file_id length: {len(video.file_id)} characters")
        print()
        
        # Update to correct file_id
        video.file_id = CORRECT_FILE_ID
        db.commit()
        
        print("✅ Updated successfully!")
        print(f"New file_id: {video.file_id}")
        print(f"New file_id length: {len(video.file_id)} characters")
        print()
        print("🎉 Now restart your bot and test /video command!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_file_id()
