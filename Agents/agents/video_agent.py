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
            
            # Prepare caption
            caption = (f"📹 **{video.title}**\n\n{video.description}\n\n"
                      f"{duration_text}"
                      f"Difficulty: {'⭐' * video.difficulty_level}\n\n"
                      f"Watch this video and then use /quiz to test your understanding!")
            
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
                # Send local file
                with open(video_source, "rb") as video_file:
                    logger.info(f"Opening local file: {video_source} (size: {os.path.getsize(video_source)} bytes)")
                    message = await self.bot.send_video(
                        chat_id=telegram_id,
                        video=video_file,
                        caption=caption
                    )
            else:
                # Send Telegram file_id or URL
                message = await self.bot.send_video(
                    chat_id=telegram_id,
                    video=video_source,
                    caption=caption
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
            logger.error(f"Error sending video (file_id/path: {video.file_id if 'video' in locals() else 'unknown'}): {str(e)}")
            logger.exception(e)  # Log full traceback
            return {
                "success": False,
                "error": str(e)
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
