"""
Video Sending Agent - Manages daily video delivery to users
"""
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import os
import re
from pathlib import Path
from loguru import logger

from database.operations import (
    get_user_by_telegram_id,
    get_next_video_for_user,
    mark_video_watched
)
from config.settings import VIDEO_AGENT_PROMPT

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    import requests


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
        Send the next video to a user
        
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
            
            # Determine file_id type and send appropriately
            file_identifier = video.file_id.strip()
            video_source = None
            send_method = None
            
            # 1. Check if it's a Telegram file_id (starts with common prefixes)
            telegram_file_id_pattern = r'^(BAAC|AgAC|CgAC|AwAC|DgAC|DQA|CQAD|BQAD|BQAC)'
            if re.match(telegram_file_id_pattern, file_identifier, re.IGNORECASE):
                logger.info(f"Detected Telegram file_id for video {video.id}: {file_identifier[:20]}...")
                video_source = file_identifier
                send_method = "telegram_file_id"
            
            # 2. Check if it's a URL (http/https)
            elif file_identifier.startswith(('http://', 'https://')):
                logger.info(f"Detected URL for video {video.id}: {file_identifier}")
                
                # Validate URL reachability
                is_reachable = await self._check_url_reachable(file_identifier)
                if not is_reachable:
                    logger.error(f"URL is not reachable: {file_identifier}")
                    return {
                        "success": False,
                        "error": f"Video URL is not accessible: {file_identifier}"
                    }
                
                video_source = file_identifier
                send_method = "url"
            
            # 3. Assume it's a local file path
            else:
                logger.info(f"Detected local file path for video {video.id}: {file_identifier}")
                
                # Check if file exists
                if not os.path.exists(file_identifier):
                    logger.error(f"Local file does not exist: {file_identifier}")
                    return {
                        "success": False,
                        "error": f"Video file not found: {file_identifier}"
                    }
                
                # Check if it's a file (not directory)
                if not os.path.isfile(file_identifier):
                    logger.error(f"Path is not a file: {file_identifier}")
                    return {
                        "success": False,
                        "error": f"Invalid video file path: {file_identifier}"
                    }
                
                video_source = file_identifier
                send_method = "local_file"
            
            # Send video based on detected type
            logger.info(f"Sending video {video.id} to user {telegram_id} using method: {send_method}")
            
            if send_method == "local_file":
                # Send local file with extended timeout for large files
                file_size = os.path.getsize(video_source)
                file_size_mb = file_size / (1024 * 1024)
                
                # Calculate timeout: 30s base + 10s per MB
                timeout = max(60, 30 + int(file_size_mb * 10))
                logger.info(f"Opening local file: {video_source} (size: {file_size_mb:.2f} MB, timeout: {timeout}s)")
                
                with open(video_source, "rb") as video_file:
                    message = await self.bot.send_video(
                        chat_id=telegram_id,
                        video=video_file,
                        caption=caption,
                        read_timeout=timeout,
                        write_timeout=timeout,
                        connect_timeout=30,
                        pool_timeout=30
                    )
            else:
                # Send Telegram file_id or URL
                message = await self.bot.send_video(
                    chat_id=telegram_id,
                    video=video_source,
                    caption=caption,
                    read_timeout=30,
                    write_timeout=30
                )
            
            # Track video delivery in memory
            self.active_deliveries[telegram_id] = {
                "video_id": video.id,
                "sent_at": datetime.utcnow(),
                "user_id": user.id
            }
            
            # Mark video as started (in progress) in database so quiz can access it
            mark_video_watched(user.id, video.id, completed=False, watch_time=0)
            
            logger.info(f"Successfully sent video {video.id} to user {telegram_id} via {send_method}")
            
            return {
                "success": True,
                "video_id": video.id,
                "title": video.title,
                "message": "Video sent successfully"
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error sending video (file_id/path: {video.file_id if 'video' in locals() else 'unknown'}): {error_msg}")
            logger.exception(e)  # Log full traceback
            
            # Provide user-friendly error messages
            if "caption is too long" in error_msg.lower():
                error_msg = "Video caption was too long. Please contact support."
            elif "timed out" in error_msg.lower():
                error_msg = "Video upload timed out. The file may be too large. Please try again."
            elif "file not found" in error_msg.lower():
                error_msg = "Video file not found. Please contact support."
            
            return {
                "success": False,
                "error": error_msg
            }
    
    async def _check_url_reachable(self, url: str) -> bool:
        """
        Check if a URL is reachable
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is reachable, False otherwise
        """
        try:
            if HAS_AIOHTTP:
                # Use async aiohttp for better performance
                async with aiohttp.ClientSession() as session:
                    async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        return response.status < 400
            else:
                # Fallback to synchronous requests
                response = requests.head(url, timeout=10, allow_redirects=True)
                return response.status_code < 400
        except Exception as e:
            logger.warning(f"URL check failed for {url}: {str(e)}")
            return False
    
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
