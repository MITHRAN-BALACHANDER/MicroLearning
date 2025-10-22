import sqlite3
import os

# Use local file path instead of Telegram file_id
video_file_path = r"data\videos\WhatsApp Video 2025-10-22 at 10.28.11_aa628e17.mp4"

# Get absolute path
abs_path = os.path.abspath(video_file_path)

print(f"Setting video file_id to local path:")
print(f"  {abs_path}")
print(f"  File exists: {os.path.exists(abs_path)}")
print(f"  File size: {os.path.getsize(abs_path):,} bytes")
print()

# Update database
conn = sqlite3.connect('microlearning.db')
cursor = conn.cursor()

cursor.execute("UPDATE videos SET file_id = ? WHERE id = 1", (abs_path,))
conn.commit()

# Verify
cursor.execute("SELECT id, title, file_id FROM videos WHERE id = 1")
result = cursor.fetchone()

if result:
    vid_id, title, file_id = result
    print("✅ Updated successfully!")
    print(f"   Video ID: {vid_id}")
    print(f"   Title: {title}")
    print(f"   file_id: {file_id}")
    print(f"   Type: Local file path")
else:
    print("❌ Video not found!")

conn.close()

print("\n🚀 Now restart your bot and test /video")
print("   The bot will upload the file from your local disk")
print("   After first upload, you can optionally save the new file_id")
