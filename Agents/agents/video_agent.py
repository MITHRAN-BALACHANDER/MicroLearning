"""
Video Sending Agent - Manages daily video delivery to users

Platform-agnostic: the learner's UserRef decides whether the video goes out
over Telegram or WhatsApp, and which cached media reference is used.
"""
from typing import Any, Dict
from datetime import datetime
from loguru import logger

from database.operations import (
    get_user_by_ref,
    get_next_video_for_user,
    get_media_ref,
    mark_video_watched
)
from config.settings import AUTO_UPLOAD_MEDIA
from messaging.base import UserRef


class VideoAgent:
    """
    Dynamic agent responsible for:
    - Sending daily videos to users on any enabled platform
    - Tracking video progress
    - Personalizing content delivery
    """

    def __init__(self, router, upload_agent=None, delivery_agent=None):
        self.router = router
        self.name = "VideoAgent"
        self.description = "Manages video content delivery and tracking"
        self.active_deliveries = {}

        if upload_agent is None:
            from agents.video_upload_agent import VideoUploadAgent
            upload_agent = VideoUploadAgent(router)
        if delivery_agent is None:
            from agents.video_delivery_agent import VideoDeliveryAgent
            delivery_agent = VideoDeliveryAgent(router)

        self.upload_agent = upload_agent
        self.delivery_agent = delivery_agent
        logger.info(f"Initialized {self.name}")

    def build_caption(self, video, max_chars: int) -> str:
        """
        Build a caption that fits the platform's media caption limit
        (1024 characters on both Telegram and WhatsApp today).
        """
        duration_text = ""
        if video.duration:
            minutes = video.duration // 60
            seconds = video.duration % 60
            duration_text = f"Duration: {minutes}:{seconds:02d}\n"

        title = video.title[:100] if video.title else "Video"
        description = video.description or "Educational video"

        base_text = f"{title}\n\n"
        difficulty_stars = '*' * (video.difficulty_level or 1)
        footer_text = (f"\n{duration_text}"
                       f"Difficulty: {difficulty_stars}\n\n"
                       f"Watch this video and then send /quiz to test your understanding!")

        # Leave a 10 character safety buffer under the platform limit
        available_space = max_chars - len(base_text) - len(footer_text) - 10

        if len(description) > available_space:
            description = description[:max(0, available_space - 3)] + "..."

        caption = base_text + description + footer_text

        if len(caption) > max_chars:
            caption = caption[:max_chars - 3] + "..."
            logger.warning(f"Caption truncated to {max_chars} chars for video {video.id}")

        return caption

    async def resolve_media_ref(self, video, ref: UserRef) -> Dict[str, Any]:
        """
        Find the media reference for this video on the learner's platform,
        uploading once if AUTO_UPLOAD_MEDIA is enabled and none is cached.
        """
        platform = ref.platform.value

        media_ref = get_media_ref(video.id, platform)
        if media_ref:
            return {"success": True, "media_ref": media_ref}

        if not AUTO_UPLOAD_MEDIA:
            return {
                "success": False,
                "error": f"This video has not been published to {platform} yet.",
                "suggestion": f"Run the upload agent for video {video.id} on {platform}.",
            }

        logger.info(f"No cached {platform} media for video {video.id} - uploading now")
        result = await self.upload_agent.ensure_media_ref(video.id, ref.platform)

        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", f"Could not publish this video to {platform}."),
                "suggestion": result.get("suggestion", ""),
            }

        return {"success": True, "media_ref": result["media_ref"]}

    async def send_daily_video(self, ref: UserRef) -> Dict[str, Any]:
        """
        Send the next video to a learner using their platform's cached media ref

        Args:
            ref: UserRef identifying the learner and platform

        Returns:
            Dict with status and video info
        """
        video = None
        try:
            user = get_user_by_ref(ref)
            if not user:
                return {
                    "success": False,
                    "error": "User not found. Please send /start first."
                }

            video = get_next_video_for_user(user.id)
            if not video:
                return {
                    "success": False,
                    "error": "No more videos available. You've completed all content!"
                }

            resolved = await self.resolve_media_ref(video, ref)
            if not resolved["success"]:
                logger.error(
                    f"No media reference for video {video.id} on {ref.platform.value}: "
                    f"{resolved['error']}"
                )
                return {
                    "success": False,
                    "error": resolved["error"],
                    "suggestion": resolved.get("suggestion", ""),
                }

            client = self.router.client_for(ref)
            caption = self.build_caption(video, client.max_caption_chars)

            delivery = await self.delivery_agent.send_video_by_media_ref(
                ref=ref,
                media_ref=resolved["media_ref"],
                caption=caption,
                video_metadata={"video_id": video.id, "title": video.title},
            )

            if not delivery["success"]:
                return {
                    "success": False,
                    "error": delivery.get("error", "Video delivery failed."),
                    "suggestion": delivery.get("suggestion", ""),
                }

            # Track video delivery in memory
            self.active_deliveries[ref.key] = {
                "video_id": video.id,
                "sent_at": datetime.utcnow(),
                "user_id": user.id,
                "platform": ref.platform.value,
            }

            # Mark video as started (in progress) so /quiz can find it
            mark_video_watched(user.id, video.id, completed=False, watch_time=0)

            logger.info(
                f"Successfully sent video {video.id} to {ref} on {ref.platform.value}"
            )

            return {
                "success": True,
                "video_id": video.id,
                "title": video.title,
                "platform": ref.platform.value,
                "message": "Video sent successfully"
            }

        except Exception as e:
            logger.exception(
                f"Error sending video {video.id if video else 'unknown'} to {ref}: {e}"
            )
            return {
                "success": False,
                "error": "An error occurred while delivering the video."
            }

    async def mark_video_completed(self, ref: UserRef, video_id: int,
                                   watch_time: int = 0) -> Dict[str, Any]:
        """Mark a video as completed by a user"""
        try:
            user = get_user_by_ref(ref)
            if not user:
                return {"success": False, "error": "User not found"}

            mark_video_watched(user.id, video_id, completed=True, watch_time=watch_time)

            self.active_deliveries.pop(ref.key, None)

            logger.info(f"Marked video {video_id} as completed for {ref}")

            return {"success": True, "message": "Video marked as completed"}

        except Exception as e:
            logger.error(f"Error marking video completed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_user_video_progress(self, ref: UserRef) -> Dict[str, Any]:
        """Get video progress for a user"""
        try:
            user = get_user_by_ref(ref)
            if not user:
                return {"success": False, "error": "User not found"}

            from database.operations import get_user_progress
            progress = get_user_progress(user.id)

            return {"success": True, "progress": progress}

        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            return {"success": False, "error": str(e)}

    async def schedule_daily_videos(self):
        """Schedule videos to be sent daily (called by scheduler)"""
        logger.info("Running daily video scheduler...")
        # Note: on WhatsApp an unprompted push only reaches learners inside the
        # 24h customer service window; outside it an approved template message
        # is required (see docs/WHATSAPP_SETUP.md).
        pass

    def get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return {
            "name": self.name,
            "active_deliveries": len(self.active_deliveries),
            "platforms": [p.value for p in self.router.platforms],
            "status": "active"
        }
