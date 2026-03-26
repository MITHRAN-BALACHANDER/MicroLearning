"""
Video Sending Agent - Manages daily video delivery to users
"""
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import os
from pathlib import Path
from loguru import logger

from database.operations import (
    get_user_by_telegram_id,
    get_next_video_for_user,
    mark_video_watched
)
from config.settings import VIDEO_AGENT_PROMPT

class VideoAgent:
    """
    Dynamic agent responsible for:
    - Sending daily videos to users
    - Tracking video progress
    - Personalizing content delivery
    """
    
    def __init__(self, telegram_bot):
        self.bot = telegram_bot
        self.name = "VideoAgent"
        self.description = "Manages video content delivery and tracking"
        self.active_deliveries = {}
        logger.info(f"Initialized {self.name}")
    
    async def send_daily_video(self, telegram_id: str) -> Dict[str, Any]:
        """
        Send the next video to a user using cached file_id
        
        Args:
            telegram_id: User's Telegram ID
            
        Returns:
            Dict with status and video info
        """
        try:
            # Get user from database
            user = get_user_by_telegram_id(telegram_id)
            if not user:
                return {
                    "success": False,
                    "error": "User not found. Please use /start first."
                }
            
            # Get next video for user
            video = get_next_video_for_user(user.id)
            if not video:
                return {
                    "success": False,
                    "error": "No more videos available. You've completed all content!"
                }
            
            # Format duration if available
            duration_text = ""
            if video.duration:
                minutes = video.duration // 60
                seconds = video.duration % 60
                duration_text = f"Duration: {minutes}:{seconds:02d}\n"
            
            # Prepare caption with Telegram's 1024 character limit
            title = video.title[:100] if video.title else "Video"
            description = video.description or "Educational video"
            
            # Build caption components
            base_text = f"{title}\n\n"
            difficulty_stars = '*' * video.difficulty_level
            footer_text = (f"\n{duration_text}"
                          f"Difficulty: {difficulty_stars}\n\n"
                          f"Watch this video and then use /quiz to test your understanding!")
            
            # Calculate available space for description (1024 char Telegram limit)
            available_space = 1024 - len(base_text) - len(footer_text) - 10  # 10 char safety buffer
            
            # Truncate description if needed
            if len(description) > available_space:
                description = description[:max(0, available_space - 3)] + "..."
            
            # Build final caption
            caption = base_text + description + footer_text
            
            # Final safety check - ensure caption doesn't exceed 1024 chars
            if len(caption) > 1024:
                caption = caption[:1021] + "..."
                logger.warning(f"Caption truncated to 1024 chars for video {video.id}")
            
            # Send using cached file_id only
            file_id = video.file_id
            
            if not file_id:
                logger.error(f"Video {video.id} has no file_id")
                return {
                    "success": False,
                    "error": "Video content missing. Please contact support."
                }
                
            logger.info(f"Sending video {video.id} to user {telegram_id} using cached file_id: {file_id}")
            
            try:
                message = await self.bot.send_video(
                    chat_id=telegram_id,
                    video=file_id,
                    caption=caption,
                    read_timeout=30,
                    write_timeout=30
                )
            except Exception as e:
                 # Check for timeout specifically
                error_msg = str(e).lower()
                if "timed out" in error_msg:
                    logger.error(f"Network timeout sending cached file_id {file_id}")
                    return {
                        "success": False,
                        "error": "Video delivery failed due to network timeout. Retrying via cached delivery."
                    }
                raise e
            
            # Track video delivery in memory
            self.active_deliveries[telegram_id] = {
                "video_id": video.id,
                "sent_at": datetime.utcnow(),
                "user_id": user.id
            }
            
            # Mark video as started (in progress) in database so quiz can access it
            mark_video_watched(user.id, video.id, completed=False, watch_time=0)
            
            logger.info(f"Successfully sent video {video.id} to user {telegram_id} using cached file_id")
            
            return {
                "success": True,
                "video_id": video.id,
                "title": video.title,
                "message": "Video sent successfully"
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error sending video {video.id if 'video' in locals() else 'unknown'}: {error_msg}")
            
            return {
                "success": False,
                "error": "An error occurred while delivering the video."
            }
    
    async def mark_video_completed(self, telegram_id: str, video_id: int, watch_time: int = 0) -> Dict[str, Any]:
        """
        Mark a video as completed by user
        
        Args:
            telegram_id: User's Telegram ID
            video_id: Video ID
            watch_time: Time watched in seconds
            
        Returns:
            Dict with status
        """
        try:
            user = get_user_by_telegram_id(telegram_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            mark_video_watched(user.id, video_id, completed=True, watch_time=watch_time)
            
            # Clean up active delivery
            if telegram_id in self.active_deliveries:
                del self.active_deliveries[telegram_id]
            
            logger.info(f"Marked video {video_id} as completed for user {telegram_id}")
            
            return {
                "success": True,
                "message": "Video marked as completed"
            }
            
        except Exception as e:
            logger.error(f"Error marking video completed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_user_video_progress(self, telegram_id: str) -> Dict[str, Any]:
        """Get video progress for a user"""
        try:
            user = get_user_by_telegram_id(telegram_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            from database.operations import get_user_progress
            progress = get_user_progress(user.id)
            
            return {
                "success": True,
                "progress": progress
            }
            
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def schedule_daily_videos(self):
        """Schedule videos to be sent daily (called by scheduler)"""
        logger.info("Running daily video scheduler...")
        # This would integrate with your user notification system
        # For now, users request videos with /video command
        pass
    
    def get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return {
            "name": self.name,
            "active_deliveries": len(self.active_deliveries),
            "status": "active"
        }
