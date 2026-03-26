"""
Production-Ready Video Upload & Delivery System - Integration Example

This demonstrates how to use VideoUploadAgent and VideoDeliveryAgent
for a reliable, scalable video delivery system.

CRITICAL UNDERSTANDING:
-----------------------
1. VideoUploadAgent: Upload video ONCE, get file_id, cache it
2. VideoDeliveryAgent: Send to users using cached file_id (no re-upload)
3. Never re-upload the same video per user
4. Store file_id in database for persistence

ROOT CAUSE OF TIMEOUTS:
-----------------------
- Windows async file I/O + httpx = blocking issues
- OneDrive sync interference during file streaming
- Opening files in async handlers causes write timeouts
- Solution: Buffer file in memory, use file_id for delivery

ARCHITECTURE:
-------------
┌─────────────────────┐
│  Admin adds video   │
│  (local file path)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│  VideoUploadAgent               │
│  - Upload ONCE to Telegram      │
│  - Extract file_id              │
│  - Cache in memory + DB         │
└──────────┬──────────────────────┘
           │ file_id
           ▼
┌─────────────────────────────────┐
│  Database                       │
│  videos.file_id = "BAACAgI..." │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  VideoDeliveryAgent             │
│  - Send to User 1 (file_id)    │
│  - Send to User 2 (file_id)    │
│  - Send to User N (file_id)    │
│  NO UPLOADS!                    │
└─────────────────────────────────┘
"""

import asyncio
import os
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
from loguru import logger

from agents.video_upload_agent import VideoUploadAgent
from agents.video_delivery_agent import VideoDeliveryAgent
from database.operations import get_video_by_id, get_user_by_telegram_id, add_video

# ============================================================================
# STEP 1: Initialize Agents (do this once at bot startup)
# ============================================================================

async def initialize_agents(bot: Bot):
    """
    Initialize upload and delivery agents
    
    Args:
        bot: Telegram Bot instance
        
    Returns:
        Tuple of (upload_agent, delivery_agent)
    """
    upload_agent = VideoUploadAgent(bot)
    delivery_agent = VideoDeliveryAgent(bot)
    
    logger.info("Video agents initialized")
    return upload_agent, delivery_agent


# ============================================================================
# STEP 2: Admin Command - Upload New Video (One-Time Upload)
# ============================================================================

async def admin_upload_video_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    upload_agent: VideoUploadAgent
):
    """
    Admin command to upload a new video and cache its file_id
    
    Usage: /adminupload C:/Videos/tutorial.mp4 "Python Basics" "Learn Python fundamentals"
    
    This is done ONCE per video by an admin/system.
    Regular users NEVER trigger uploads.
    """
    user_id = str(update.effective_user.id)
    
    # Check if user is admin (implement your own auth)
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Admin only command")
        return
    
    # Parse arguments
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /adminupload <file_path> <title> <description>\n"
            "Example: /adminupload C:/Videos/video.mp4 \"Title\" \"Description\""
        )
        return
    
    file_path = context.args[0]
    title = context.args[1]
    description = " ".join(context.args[2:])
    
    # Validate file exists
    if not os.path.exists(file_path):
        await update.message.reply_text(f"❌ File not found: {file_path}")
        return
    
    # Check if OneDrive path (WARNING)
    if "OneDrive" in file_path or "onedrive" in file_path.lower():
        await update.message.reply_text(
            "⚠️ WARNING: File is in OneDrive folder!\n"
            "OneDrive sync can cause upload timeouts.\n"
            "RECOMMENDED: Move file to C:/Videos/ or another local folder.\n\n"
            "Continue anyway? Reply /forceupload to proceed."
        )
        return
    
    await update.message.reply_text(f"📤 Uploading {os.path.basename(file_path)}...\nThis may take 1-3 minutes...")
    
    # Upload and cache file_id
    result = await upload_agent.upload_and_cache_video(
        file_path=file_path,
        test_chat_id=user_id,  # Upload to admin's chat first
        max_retries=3,
        enable_streaming=True
    )
    
    if result["success"]:
        file_id = result["file_id"]
        file_size_mb = result.get("file_size_mb", 0)
        
        # Save to database with file_id
        try:
            video = add_video(
                title=title,
                description=description,
                file_id=file_id,  # Store the Telegram file_id
                file_path=file_path  # Optional: keep local path reference
            )
            
            await update.message.reply_text(
                f"✅ Video uploaded successfully!\n\n"
                f"📹 Title: {title}\n"
                f"💾 Size: {file_size_mb:.2f} MB\n"
                f"🆔 Video ID: {video.id}\n"
                f"🔑 file_id: {file_id[:30]}...\n\n"
                f"✨ This video can now be delivered to unlimited users instantly!"
            )
            
            logger.info(f"Video {video.id} uploaded and cached: {file_id[:30]}...")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to save to database: {e}")
            logger.error(f"Database error: {e}")
    else:
        error_msg = result.get("error", "Unknown error")
        await update.message.reply_text(
            f"❌ Upload failed: {error_msg}\n\n"
            f"Troubleshooting:\n"
            f"1. Ensure file is not in OneDrive\n"
            f"2. Check file is not corrupted\n"
            f"3. Verify file size < 50MB\n"
            f"4. Check internet connection"
        )
        logger.error(f"Upload failed: {error_msg}")


# ============================================================================
# STEP 3: User Command - Send Video (Fast Delivery via file_id)
# ============================================================================

async def video_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    delivery_agent: VideoDeliveryAgent
):
    """
    User command to receive next video
    
    Usage: /video
    
    This sends videos using cached file_id - NO UPLOAD, instant delivery.
    """
    telegram_id = str(update.effective_user.id)
    
    try:
        # Get user from database
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            await update.message.reply_text("Please use /start first to register")
            return
        
        # Get next video for user (your own logic here)
        video = get_next_video_for_user(user.id)
        if not video:
            await update.message.reply_text("🎉 You've completed all videos!")
            return
        
        # Check if video has file_id
        if not video.file_id:
            await update.message.reply_text(
                "❌ Video not uploaded yet. Please contact admin."
            )
            logger.error(f"Video {video.id} has no file_id!")
            return
        
        # Prepare caption
        caption = f"📚 {video.title}\n\n{video.description}\n\n⭐ Use /quiz to test your understanding!"
        
        # Deliver video using file_id (FAST - no upload)
        await update.message.reply_text("📹 Sending your video...")
        
        result = await delivery_agent.send_video_by_file_id(
            chat_id=telegram_id,
            file_id=video.file_id,
            caption=caption,
            video_metadata={"video_id": video.id, "title": video.title},
            max_retries=3
        )
        
        if result["success"]:
            logger.info(f"Video {video.id} delivered to user {telegram_id}")
            # Mark video as watched in database
            # mark_video_watched(user.id, video.id)
        else:
            error_msg = result.get("error", "Unknown error")
            suggestion = result.get("suggestion", "")
            
            await update.message.reply_text(
                f"❌ Failed to send video: {error_msg}\n\n{suggestion}"
            )
            logger.error(f"Delivery failed: {error_msg}")
            
    except Exception as e:
        logger.exception(f"Error in video_command: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again or contact support."
        )


# ============================================================================
# STEP 4: Helper Functions
# ============================================================================

def is_admin(user_id: str) -> bool:
    """
    Check if user is admin
    
    Implement your own logic:
    - Check against ADMIN_USER_IDS in config
    - Query database for user role
    - Check environment variable
    """
    ADMIN_IDS = os.getenv("ADMIN_USER_IDS", "").split(",")
    return user_id in ADMIN_IDS


def get_next_video_for_user(user_id: int):
    """
    Get next unwatched video for user
    
    Implement your own logic:
    - Query videos not in user's watch history
    - Order by difficulty/sequence
    - Return None if all watched
    """
    from database.operations import get_next_video_for_user as db_get_next
    return db_get_next(user_id)


# ============================================================================
# STEP 5: Main Bot Setup
# ============================================================================

async def post_init(application: Application):
    """
    Initialize agents after bot is ready
    """
    bot = application.bot
    upload_agent, delivery_agent = await initialize_agents(bot)
    
    # Store agents in bot_data for access in handlers
    application.bot_data["upload_agent"] = upload_agent
    application.bot_data["delivery_agent"] = delivery_agent
    
    # Optional: Load existing file_ids from database into cache
    logger.info("Loading file_ids from database into cache...")
    from database.operations import get_all_videos
    videos = get_all_videos()
    for video in videos:
        if video.file_id and video.file_path:
            upload_agent.cache_file_id(video.file_path, video.file_id)
    logger.info(f"Cached {len(videos)} file_ids from database")


def main():
    """
    Main entry point
    """
    # Load token from environment
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set!")
    
    # Create application
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # Add command handlers
    application.add_handler(
        CommandHandler("adminupload", 
                      lambda u, c: admin_upload_video_command(u, c, application.bot_data["upload_agent"]))
    )
    application.add_handler(
        CommandHandler("video",
                      lambda u, c: video_command(u, c, application.bot_data["delivery_agent"]))
    )
    
    # Start bot
    logger.info("Starting bot...")
    application.run_polling()


# ============================================================================
# PRODUCTION BEST PRACTICES
# ============================================================================

"""
✅ DO:
------
1. Upload videos ONCE via VideoUploadAgent
2. Store file_id in database immediately
3. Use VideoDeliveryAgent with file_id for all users
4. Move video files OUT of OneDrive to C:/Videos/ or similar
5. Enable supports_streaming=True for better UX
6. Cache file_ids on bot startup from database
7. Use proper error handling and retry logic
8. Log all operations for debugging

❌ DON'T:
---------
1. Re-upload same video per user (wastes time, bandwidth, fails)
2. Store videos in OneDrive (sync causes I/O issues)
3. Increase timeout blindly (doesn't fix root cause)
4. Use local file paths in send_video for multiple users
5. Ignore file_id mechanism
6. Block event loop with long file operations
7. Send "file too large" lies when real issue is timeout

MIGRATION PATH (Existing Videos):
----------------------------------
If you have videos already uploaded:

1. Extract file_id from old messages:
   - Forward video to @getidsbot on Telegram
   - Or check bot logs for file_id in old sends
   
2. Update database:
   UPDATE videos SET file_id = 'BAACAgI...' WHERE id = 1;
   
3. Use VideoDeliveryAgent for all future sends

4. Optional: Remove local file_path references once file_ids stored

MONITORING:
-----------
Check agent stats regularly:

upload_stats = upload_agent.get_upload_stats()
delivery_stats = delivery_agent.get_delivery_stats()

logger.info(f"Uploads: {upload_stats['total_uploads']}")
logger.info(f"Deliveries: {delivery_stats['total_sent']}")
logger.info(f"Success rate: {delivery_stats['success_rate']:.1f}%")
"""

if __name__ == "__main__":
    main()
