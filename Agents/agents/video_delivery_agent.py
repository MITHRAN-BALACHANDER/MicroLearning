"""
Video Delivery Agent - Sends videos to users using cached file_id (no re-upload)

This agent is responsible for:
1. Delivering videos to users using cached file_id
2. Never re-uploading videos (uses file_id from cache/database)
3. Tracking video delivery state
4. Handling delivery failures with proper error messages

Key Design Principles:
- file_id is uploaded ONCE via VideoUploadAgent
- All subsequent deliveries use the cached file_id
- No blocking file I/O in delivery path
- Fast, reliable, async delivery
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from telegram import Bot
from telegram.error import TimedOut, NetworkError, TelegramError, BadRequest


class VideoDeliveryAgent:
    """
    Specialized agent for delivering videos to users via cached file_id
    """
    
    def __init__(self, telegram_bot: Bot):
        """
        Initialize delivery agent
        
        Args:
            telegram_bot: Telegram bot instance
        """
        self.bot = telegram_bot
        self.active_deliveries: Dict[str, Dict[str, Any]] = {}  # telegram_id -> delivery info
        self.delivery_stats: Dict[str, int] = {
            "total_sent": 0,
            "failed": 0,
            "retried": 0
        }
        logger.info("VideoDeliveryAgent initialized")
    
    async def send_video_by_file_id(
        self,
        chat_id: str,
        file_id: str,
        caption: str = "",
        video_metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Send video to user using Telegram file_id (no upload, instant delivery)
        
        This is the FAST path - video is already on Telegram servers.
        No file I/O, no upload, just reference existing file.
        
        Args:
            chat_id: Telegram chat/user ID
            file_id: Telegram file_id (obtained from VideoUploadAgent)
            caption: Video caption (max 1024 chars)
            video_metadata: Optional metadata (video_id, title, etc.)
            max_retries: Maximum retry attempts
            
        Returns:
            Dict with success status and message info
            
        Example:
            result = await agent.send_video_by_file_id(
                chat_id="123456789",
                file_id="BAACAgIAAxkBAAIC...",
                caption="Introduction to Python",
                video_metadata={"video_id": 1, "title": "Python Basics"}
            )
        """
        if not file_id:
            return {
                "success": False,
                "error": "file_id is required for delivery"
            }
        
        # Validate caption length
        if len(caption) > 1024:
            logger.warning(f"Caption too long ({len(caption)} chars), truncating to 1024")
            caption = caption[:1021] + "..."
        
        # Track delivery attempt
        delivery_id = f"{chat_id}_{datetime.utcnow().timestamp()}"
        self.active_deliveries[chat_id] = {
            "delivery_id": delivery_id,
            "file_id": file_id,
            "started_at": datetime.utcnow(),
            "status": "sending",
            "metadata": video_metadata
        }
        
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Sending video to {chat_id} (attempt {attempt}/{max_retries}, file_id: {file_id[:20]}...)")
                
                # Send video using file_id (FAST - no upload)
                message = await self.bot.send_video(
                    chat_id=chat_id,
                    video=file_id,
                    caption=caption,
                    supports_streaming=True,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=20,
                    pool_timeout=20
                )
                
                # Update delivery status
                self.active_deliveries[chat_id]["status"] = "delivered"
                self.active_deliveries[chat_id]["message_id"] = message.message_id
                self.active_deliveries[chat_id]["delivered_at"] = datetime.utcnow()
                
                # Update stats
                self.delivery_stats["total_sent"] += 1
                if attempt > 1:
                    self.delivery_stats["retried"] += 1
                
                logger.info(f"✅ Video delivered successfully to {chat_id} (message_id: {message.message_id})")
                
                return {
                    "success": True,
                    "message_id": message.message_id,
                    "chat_id": chat_id,
                    "file_id": file_id,
                    "attempts": attempt,
                    "delivered_at": message.date.isoformat() if message.date else None
                }
                
            except BadRequest as e:
                # BadRequest usually means invalid file_id or chat_id - don't retry
                error_msg = str(e)
                if "file_id" in error_msg.lower():
                    last_error = f"Invalid file_id - video may have been deleted from Telegram servers: {error_msg}"
                elif "chat not found" in error_msg.lower():
                    last_error = f"Chat not found - user may have blocked the bot: {error_msg}"
                else:
                    last_error = f"Bad request: {error_msg}"
                
                logger.error(f"❌ BadRequest (no retry): {last_error}")
                break  # Don't retry BadRequest errors
                
            except TimedOut as e:
                last_error = f"Delivery timed out (attempt {attempt}/{max_retries}): {str(e)}"
                logger.warning(last_error)
                if attempt < max_retries:
                    wait_time = attempt * 2
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    
            except NetworkError as e:
                last_error = f"Network error (attempt {attempt}/{max_retries}): {str(e)}"
                logger.warning(last_error)
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 3)
                    
            except TelegramError as e:
                last_error = f"Telegram error (attempt {attempt}/{max_retries}): {str(e)}"
                logger.error(last_error)
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 2)
                    
            except Exception as e:
                last_error = f"Unexpected error (attempt {attempt}/{max_retries}): {str(e)}"
                logger.error(last_error)
                logger.exception(e)
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 2)
        
        # All retries failed
        self.active_deliveries[chat_id]["status"] = "failed"
        self.active_deliveries[chat_id]["error"] = last_error
        self.delivery_stats["failed"] += 1
        
        logger.error(f"❌ Video delivery failed after {max_retries} attempts: {last_error}")
        
        # Return truthful error message
        return {
            "success": False,
            "error": last_error,
            "chat_id": chat_id,
            "attempts": max_retries,
            "suggestion": self._get_error_suggestion(last_error)
        }
    
    def _get_error_suggestion(self, error_msg: str) -> str:
        """
        Provide helpful suggestions based on error type
        
        Args:
            error_msg: Error message
            
        Returns:
            User-friendly suggestion
        """
        error_lower = error_msg.lower()
        
        if "invalid file_id" in error_lower or "file_id" in error_lower:
            return "The video file_id is invalid. Please re-upload the video using VideoUploadAgent."
        elif "chat not found" in error_lower or "blocked" in error_lower:
            return "Cannot reach user. They may have blocked the bot or deleted their account."
        elif "timed out" in error_lower or "timeout" in error_lower:
            return "Network timeout. Please check your internet connection and try again."
        elif "network" in error_lower:
            return "Network error. Please verify your connection and Telegram API status."
        else:
            return "An unexpected error occurred. Please check logs for details."
    
    async def send_video_by_url(
        self,
        chat_id: str,
        video_url: str,
        caption: str = "",
        video_metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Send video to user using URL (Telegram will fetch and cache)
        
        Note: First time sending a URL, Telegram caches it and returns file_id.
        Subsequent sends should use the file_id for faster delivery.
        
        Args:
            chat_id: Telegram chat/user ID
            video_url: Public URL to video file
            caption: Video caption
            video_metadata: Optional metadata
            max_retries: Maximum retry attempts
            
        Returns:
            Dict with success status and extracted file_id
        """
        if not video_url.startswith(('http://', 'https://')):
            return {
                "success": False,
                "error": "Invalid video URL - must start with http:// or https://"
            }
        
        # Validate caption
        if len(caption) > 1024:
            caption = caption[:1021] + "..."
        
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Sending video URL to {chat_id} (attempt {attempt}/{max_retries})")
                
                message = await self.bot.send_video(
                    chat_id=chat_id,
                    video=video_url,
                    caption=caption,
                    supports_streaming=True,
                    read_timeout=60,
                    write_timeout=60
                )
                
                # Extract file_id for future use
                file_id = message.video.file_id if message.video else None
                
                logger.info(f"✅ Video URL delivered, extracted file_id: {file_id[:20] if file_id else 'N/A'}...")
                
                return {
                    "success": True,
                    "message_id": message.message_id,
                    "file_id": file_id,  # IMPORTANT: Cache this for future sends
                    "video_url": video_url,
                    "attempts": attempt
                }
                
            except Exception as e:
                last_error = f"Error sending URL (attempt {attempt}/{max_retries}): {str(e)}"
                logger.warning(last_error)
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 3)
        
        return {
            "success": False,
            "error": last_error,
            "attempts": max_retries
        }
    
    def get_active_delivery(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active delivery info for a user
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            Delivery info dict or None
        """
        return self.active_deliveries.get(chat_id)
    
    def clear_active_delivery(self, chat_id: str) -> bool:
        """
        Clear active delivery for a user
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            True if cleared, False if not found
        """
        if chat_id in self.active_deliveries:
            del self.active_deliveries[chat_id]
            logger.info(f"Cleared active delivery for {chat_id}")
            return True
        return False
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """
        Get delivery statistics
        
        Returns:
            Dict with delivery metrics
        """
        return {
            **self.delivery_stats,
            "active_deliveries": len(self.active_deliveries),
            "success_rate": (
                (self.delivery_stats["total_sent"] / 
                 (self.delivery_stats["total_sent"] + self.delivery_stats["failed"]) * 100)
                if (self.delivery_stats["total_sent"] + self.delivery_stats["failed"]) > 0
                else 0
            )
        }
