import sqlite3

# The FULL correct file_id
correct_file_id = "BAACAgUAAxkBAAEYkKNo-HHjoy8w1dgnhlZ9VNsR-2FQfAACpxgAAiIGyFeB48pUoTaIxzYE"

print(f"Updating database with file_id:")
print(f"  {correct_file_id}")
print(f"  Length: {len(correct_file_id)} characters")
print()

# Connect and update
conn = sqlite3.connect('microlearning.db')
cursor = conn.cursor()

# Update the file_id
cursor.execute("UPDATE videos SET file_id = ? WHERE id = 1", (correct_file_id,))
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
    print(f"   Length: {len(file_id)} characters")
    
    if file_id == correct_file_id:
        print("\n🎉 Perfect! file_id matches exactly!")
    else:
        print(f"\n⚠️  Warning: file_id doesn't match!")
        print(f"   Expected: {correct_file_id}")
        print(f"   Got: {file_id}")
else:
    print("❌ Video not found!")

conn.close()

print("\n🚀 Now restart your bot: python main.py")
