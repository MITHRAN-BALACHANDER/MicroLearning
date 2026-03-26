"""
QUICK START GUIDE - Video Upload & Delivery System
===================================================

Get your Telegram bot sending videos reliably in 5 minutes!
"""

# ============================================================================
# STEP 1: Setup (One-Time)
# ============================================================================

"""
1.1 Your videos are already in the correct location!

✅ CURRENT: C:/Users/bmith/OneDrive/Desktop/projects -2025/MicroLearning/Agents/data/videos/
✅ USE:     Relative path from project: "data/videos/your_video.mp4"

Note: While the project is in OneDrive, videos are accessed via relative paths
which minimizes OneDrive sync issues. The memory buffering technique in
VideoUploadAgent handles any remaining I/O latency.

To list your videos:
    Get-ChildItem "data\videos\*.mp4"
"""

# ============================================================================
# STEP 2: Initialize Agents in Your Bot
# ============================================================================

"""
Add to your main.py or bot initialization:
"""

from telegram import Bot
from agents.video_upload_agent import VideoUploadAgent
from agents.video_delivery_agent import VideoDeliveryAgent

async def initialize_bot():
    # Create bot
    bot = Bot(token="YOUR_BOT_TOKEN")
    
    # Initialize agents
    upload_agent = VideoUploadAgent(bot)
    delivery_agent = VideoDeliveryAgent(bot)
    
    # Store in application context
    application.bot_data["upload_agent"] = upload_agent
    application.bot_data["delivery_agent"] = delivery_agent
    
    # Optional: Load existing file_ids from database
    from database.operations import get_all_videos
    videos = get_all_videos()
    for video in videos:
        if video.file_id and video.file_path:
            upload_agent.cache_file_id(video.file_path, video.file_id)
    
    print(f"✅ Agents initialized, cached {len(videos)} file_ids")

# ============================================================================
# STEP 3: Add Admin Upload Command (One-Time Per Video)
# ============================================================================

"""
Admin command to upload new videos to the system.
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage: /adminupload data/videos/Learning_6977a978.mp4 "Python Basics" "Introduction to Python"
    Or:    /adminupload "C:/Users/bmith/OneDrive/Desktop/projects -2025/MicroLearning/Agents/data/videos/Learning_6977a978.mp4" "Python Basics" "Introduction"
    """
    user_id = str(update.effective_user.id)
    
    # Check admin (implement your auth)
    if user_id not in ["YOUR_ADMIN_ID"]:
        await update.message.reply_text("⛔ Admin only")
        return
    
    # Parse arguments
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /adminupload <path> <title> <description>"
        )
        return
    
    file_path = context.args[0]
    title = context.args[1]
    description = " ".join(context.args[2:])
    
    # If relative path, make it absolute from project root
    if not os.path.isabs(file_path):
        project_root = r"C:\Users\bmith\OneDrive\Desktop\projects -2025\MicroLearning\Agents"
        file_path = os.path.join(project_root, file_path)
    
    # Validate file
    if not os.path.exists(file_path):
        await update.message.reply_text(f"❌ File not found: {file_path}")
        return
    
    # Upload and extract file_id
    await update.message.reply_text("📤 Uploading...")
    
    upload_agent = context.bot_data["upload_agent"]
    result = await upload_agent.upload_and_cache_video(
        file_path=file_path,
        test_chat_id=user_id  # Upload to your chat first
    )
    
    if result["success"]:
        file_id = result["file_id"]
        
        # Save to database
        from database.operations import add_video
        video = add_video(
            title=title,
            description=description,
            file_id=file_id,
            file_path=file_path
        )
        
        await update.message.reply_text(
            f"✅ Uploaded!\n"
            f"Video ID: {video.id}\n"
            f"file_id: {file_id[:30]}..."
        )
    else:
        await update.message.reply_text(f"❌ Failed: {result['error']}")

# Register handler
application.add_handler(CommandHandler("adminupload", admin_upload))

# ============================================================================
# STEP 4: Update User Video Command (Instant Delivery)
# ============================================================================

"""
User command to receive videos - uses cached file_id (no upload!).
"""

async def video_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage: /video
    """
    telegram_id = str(update.effective_user.id)
    
    # Get user from database
    from database.operations import get_user_by_telegram_id, get_next_video_for_user
    user = get_user_by_telegram_id(telegram_id)
    
    if not user:
        await update.message.reply_text("Please use /start first")
        return
    
    # Get next video
    video = get_next_video_for_user(user.id)
    
    if not video:
        await update.message.reply_text("🎉 All videos completed!")
        return
    
    # Check file_id exists
    if not video.file_id:
        await update.message.reply_text("❌ Video not ready. Contact admin.")
        return
    
    # Deliver using file_id (INSTANT - no upload)
    await update.message.reply_text("📹 Sending video...")
    
    delivery_agent = context.bot_data["delivery_agent"]
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
            f"❌ Delivery failed: {result['error']}\n{result.get('suggestion', '')}"
        )

# Register handler
application.add_handler(CommandHandler("video", video_command))

# ============================================================================
# STEP 5: Run Your Bot
# ============================================================================

"""
Start your bot normally:
"""

if __name__ == "__main__":
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    
    # Initialize agents (on startup)
    application.post_init = initialize_bot
    
    # Add handlers (as shown above)
    # ...
    
    # Run
    print("🚀 Bot starting...")
    application.run_polling()

# ============================================================================
# STEP 6: Test the System
# ============================================================================

"""
6.1 Upload a test video (as admin):
    
    You: /adminupload C:/Videos/test.mp4 "Test Video" "Testing upload system"
    Bot: ✅ Uploaded! Video ID: 1, file_id: BAACAgI...

6.2 Send to yourself (as user):
    
    You: /video
    Bot: 📹 Sending video...
    Bot: [Sends video INSTANTLY using file_id]

6.3 Send to another user:
    
    User: /video
    Bot: [Sends same video INSTANTLY - no re-upload!]

6.4 Check stats:
    
    upload_agent.get_upload_stats()
    # {'total_uploads': 1, 'cached_entries': 1}
    
    delivery_agent.get_delivery_stats()
    # {'total_sent': 2, 'failed': 0, 'success_rate': 100.0}
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
❌ Problem: Upload still times out

Solutions:
1. ✅ File moved out of OneDrive? Check path doesn't contain "OneDrive"
2. ✅ Internet stable? Test: ping telegram.org
3. ✅ File not corrupted? Test: open file in video player
4. ✅ File size reasonable? Telegram limit: 50 MB

❌ Problem: "Invalid file_id" error

Solutions:
1. file_id expired (rare) → Re-upload video
2. file_id from different bot → Can't transfer, must re-upload
3. Typo in file_id → Check database

❌ Problem: "Chat not found" error

Reasons:
1. User blocked bot → Mark user as inactive
2. User deleted account → Remove from database
3. Wrong chat_id → Verify Telegram ID

❌ Problem: Video takes long to send

Check:
1. Using file_id? (Fast) or file_path? (Slow)
2. file_id should be instant (<3 seconds)
3. If slow, check: video.file_id is valid Telegram file_id starting with BAAC/AgAC/etc.
"""

# ============================================================================
# PRODUCTION CHECKLIST
# ============================================================================

"""
Before deploying to production:

✅ Videos moved out of OneDrive
✅ Agents initialized on bot startup
✅ file_ids cached from database
✅ Admin upload command restricted (auth check)
✅ User delivery uses file_id (not file_path)
✅ Error handling in place
✅ Logging configured
✅ Database backups enabled
✅ Monitoring/stats checked regularly

Success criteria:
- Upload time: 20-60s (one-time per video)
- Delivery time: 1-3s per user
- Timeout rate: <5%
- Same video uploaded: 1 time (not N times for N users)
"""

# ============================================================================
# NEXT STEPS
# ============================================================================

"""
🚀 Ready to scale:

1. Distribute file_id cache:
   - Use Redis for multi-instance deployments
   - Sync cache across bot instances

2. Video CDN integration:
   - Host videos on CDN (e.g., CloudFlare)
   - Upload via URL, cache file_id

3. Analytics:
   - Track delivery success rate
   - Monitor timeout patterns
   - User engagement metrics

4. Advanced features:
   - Video transcoding (adaptive bitrate)
   - Thumbnail generation
   - Progress tracking with buttons
   - Video playlists

📚 Read full documentation:
   - docs/VIDEO_UPLOAD_DELIVERY_SYSTEM.md
   - examples/production_video_system.py

✅ You're all set! Enjoy reliable video delivery! 🎉
"""
