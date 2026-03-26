# ✅ CORRECTED PATHS - YOUR VIDEO SETUP

## 🎯 Good News: Your Videos Are Already In Place!

Your videos are located at:
```
C:\Users\bmith\OneDrive\Desktop\projects -2025\MicroLearning\Agents\data\videos\
```

### 📹 Videos Found:
- Ambition__Science_697b17f8.mp4
- Environmental_Awareness_697b17f2.mp4
- Kindness_Boomerang_697b17ff.mp4
- Learning_6977a978.mp4
- Math_Trick_697b17e2.mp4
- The_20-Second_Memory_Trick_697b1806.mp4
- WhatsApp Video 2025-10-22 at 10.28.11_aa628e17.mp4
- Wisdom_from_Literature_697b17ec.mp4

---

## 🚀 Quick Start (Updated for Your Setup)

### 1. List Your Videos

```powershell
# PowerShell
cd "C:\Users\bmith\OneDrive\Desktop\projects -2025\MicroLearning\Agents"
Get-ChildItem "data\videos\*.mp4"
```

### 2. Upload a Video (Admin Command)

```python
import os
from agents.video_upload_agent import VideoUploadAgent
from agents.video_delivery_agent import VideoDeliveryAgent

# Initialize agents
upload_agent = VideoUploadAgent(bot)
delivery_agent = VideoDeliveryAgent(bot)

# Define project root
project_root = r"C:\Users\bmith\OneDrive\Desktop\projects -2025\MicroLearning\Agents"

# Upload one of your existing videos
video_filename = "Learning_6977a978.mp4"  # Change to any video from the list above
video_path = os.path.join(project_root, "data", "videos", video_filename)

# Upload and extract file_id
result = await upload_agent.upload_and_cache_video(
    file_path=video_path,
    test_chat_id="YOUR_TELEGRAM_ID"  # Replace with your Telegram user ID
)

if result["success"]:
    file_id = result["file_id"]
    print(f"✅ Uploaded! file_id: {file_id}")
    
    # Save to database
    from database.operations import add_video
    video = add_video(
        title="Learning Video",
        description="Educational content",
        file_id=file_id,
        file_path=video_path
    )
    print(f"✅ Saved to database as video ID: {video.id}")
else:
    print(f"❌ Upload failed: {result['error']}")
```

### 3. Deliver to Users (Instant!)

```python
# Send to any user using the cached file_id
result = await delivery_agent.send_video_by_file_id(
    chat_id=user_telegram_id,
    file_id=video.file_id,
    caption="📚 Your learning video!\n\n⭐ Use /quiz to test your knowledge!"
)
```

---

## 🔧 Integration with Your Bot

Update your `/video` command handler in [main.py](main.py):

```python
async def video_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /video command - Send next video"""
    telegram_id = str(update.effective_user.id)
    
    try:
        await update.message.reply_text("📹 Fetching your next video...")
        
        # Get video from database
        from database.operations import get_user_by_telegram_id, get_next_video_for_user
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            await update.message.reply_text("Please use /start first")
            return
        
        video = get_next_video_for_user(user.id)
        if not video:
            await update.message.reply_text("🎉 You've completed all videos!")
            return
        
        # Check if video has file_id (if not, needs to be uploaded first)
        if not video.file_id:
            await update.message.reply_text(
                "❌ This video hasn't been uploaded yet.\n"
                "Admin needs to run the upload process first."
            )
            return
        
        # Use VideoDeliveryAgent for instant delivery
        delivery_agent = self.orchestrator.video_agent.delivery_agent
        result = await delivery_agent.send_video_by_file_id(
            chat_id=telegram_id,
            file_id=video.file_id,
            caption=f"📚 {video.title}\n\n{video.description}\n\n⭐ Use /quiz to test!",
            video_metadata={"video_id": video.id}
        )
        
        if result["success"]:
            # Mark as watched
            from database.operations import mark_video_watched
            mark_video_watched(user.id, video.id, completed=False)
        else:
            await update.message.reply_text(
                f"❌ Failed to send video: {result['error']}"
            )
            
    except Exception as e:
        logger.exception(f"Error in video_command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")
```

---

## 📝 Admin Command to Upload Videos

Add this command to your bot for admins:

```python
async def admin_upload_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /adminupload command - Upload video and extract file_id
    
    Usage: /adminupload data/videos/Learning_6977a978.mp4 "Title" "Description"
    """
    user_id = str(update.effective_user.id)
    
    # Check if admin (implement your own check)
    ADMIN_IDS = ["YOUR_TELEGRAM_ID"]  # Replace with actual admin IDs
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only command")
        return
    
    # Parse arguments
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /adminupload <relative_path> <title> <description>\n\n"
            "Example: /adminupload data/videos/Learning_6977a978.mp4 \"Learning\" \"Educational video\"\n\n"
            "Available videos:\n"
            "• data/videos/Learning_6977a978.mp4\n"
            "• data/videos/Math_Trick_697b17e2.mp4\n"
            "• data/videos/Ambition__Science_697b17f8.mp4"
        )
        return
    
    relative_path = context.args[0]
    title = context.args[1]
    description = " ".join(context.args[2:])
    
    # Make absolute path
    project_root = r"C:\Users\bmith\OneDrive\Desktop\projects -2025\MicroLearning\Agents"
    video_path = os.path.join(project_root, relative_path)
    
    # Validate
    if not os.path.exists(video_path):
        await update.message.reply_text(f"❌ File not found: {video_path}")
        return
    
    # Upload
    await update.message.reply_text(f"📤 Uploading {os.path.basename(video_path)}...")
    
    upload_agent = self.orchestrator.video_agent.upload_agent
    result = await upload_agent.upload_and_cache_video(
        file_path=video_path,
        test_chat_id=user_id
    )
    
    if result["success"]:
        file_id = result["file_id"]
        file_size_mb = result.get("file_size_mb", 0)
        
        # Save to database
        from database.operations import add_video
        video = add_video(
            title=title,
            description=description,
            file_id=file_id,
            file_path=video_path
        )
        
        await update.message.reply_text(
            f"✅ Success!\n\n"
            f"📹 {title}\n"
            f"💾 {file_size_mb:.2f} MB\n"
            f"🆔 Video ID: {video.id}\n"
            f"🔑 file_id: {file_id[:30]}...\n\n"
            f"✨ Now ready to deliver to unlimited users!"
        )
    else:
        await update.message.reply_text(f"❌ Upload failed: {result['error']}")
```

---

## 🔄 Migrate Existing Videos

If you have videos in the database with file_path but no file_id:

```bash
# Run migration script
python scripts/migrate_to_file_id_system.py --method upload --admin-id YOUR_TELEGRAM_ID
```

This will:
1. Find all videos without file_id
2. Upload each one and extract file_id
3. Update database automatically

---

## ✅ Testing

Test with one video first:

```python
# In Python REPL or script
import asyncio
import os
from telegram import Bot
from agents.video_upload_agent import VideoUploadAgent

async def test_upload():
    bot = Bot(token="YOUR_BOT_TOKEN")
    agent = VideoUploadAgent(bot)
    
    project_root = r"C:\Users\bmith\OneDrive\Desktop\projects -2025\MicroLearning\Agents"
    video_path = os.path.join(project_root, "data", "videos", "Learning_6977a978.mp4")
    
    result = await agent.upload_and_cache_video(
        file_path=video_path,
        test_chat_id="YOUR_TELEGRAM_ID"
    )
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"file_id: {result['file_id']}")
    else:
        print(f"Error: {result['error']}")

# Run
asyncio.run(test_upload())
```

---

## 📊 Next Steps

1. ✅ Videos are already in place (data/videos/)
2. ⏳ Add agents to your bot initialization
3. ⏳ Add admin upload command
4. ⏳ Update /video command to use delivery agent
5. ⏳ Test with one video
6. ⏳ Migrate all existing videos
7. ⏳ Deploy and monitor

---

## 💡 Key Points

1. **No need to move videos** - they're already in the right place
2. **Use relative paths** - "data/videos/video.mp4" or join with project_root
3. **Memory buffering** - VideoUploadAgent handles any OneDrive I/O issues
4. **Upload once** - Each video only needs to be uploaded once
5. **Instant delivery** - Use file_id for all user deliveries

---

**You're ready to go! Start with uploading one video to test the system.** 🚀
