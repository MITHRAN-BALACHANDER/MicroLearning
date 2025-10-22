import sys
import sqlite3

# Connect to database
conn = sqlite3.connect('microlearning.db')
cursor = conn.cursor()

# Query videos table
cursor.execute("SELECT id, title, file_id FROM videos")
videos = cursor.fetchall()

print("\n" + "="*80)
print("VIDEOS IN DATABASE")
print("="*80)

for vid in videos:
    vid_id, title, file_id = vid
    print(f"\nID: {vid_id}")
    print(f"Title: {title}")
    print(f"file_id: {file_id}")
    print(f"Length: {len(file_id)} characters")
    print(f"Starts with: {file_id[:10]}")
    
conn.close()

print("\n" + "="*80)
print("CORRECT file_id should be:")
print("BAACAgUAAxkBAAEYkKNo-HHjoy8w1dgnhlZ9VNsR-2FQfAACpxgAAiIGyFeB48pUoTaIxzYE")
print(f"Length: 84 characters")
print(f"Starts with: BAACAgUAAx")
print("="*80)
