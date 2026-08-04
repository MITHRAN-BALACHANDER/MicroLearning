"""
Video Delivery Agent - sends videos using a cached media reference (no re-upload)

This agent is responsible for:
1. Delivering videos to users using the platform's cached media reference
2. Never re-uploading videos (Telegram file_id / WhatsApp media id come from
   VideoUploadAgent)
3. Tracking video delivery state
4. Handling delivery failures with truthful, actionable error messages

Key Design Principles:
- The media handle is obtained ONCE by VideoUploadAgent, per platform
- All subsequent deliveries reuse that cached handle
- No blocking file I/O in the delivery path
- Fast, reliable, async delivery on every enabled platform
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from loguru import logger

from messaging.base import (
    MessagingError,
    PermanentMessagingError,
    Platform,
    TransientMessagingError,
    UserRef,
)


class VideoDeliveryAgent:
    """Delivers videos to learners on any enabled platform via cached media refs."""

    def __init__(self, router):
        """
        Args:
            router: MessagingRouter covering the enabled platforms
        """
        self.router = router
        self.name = "VideoDeliveryAgent"
        self.active_deliveries: Dict[str, Dict[str, Any]] = {}  # user key -> delivery info
        self.delivery_stats: Dict[str, int] = {
            "total_sent": 0,
            "failed": 0,
            "retried": 0
        }
        logger.info("VideoDeliveryAgent initialized")

    async def send_video_by_media_ref(
        self,
        ref: UserRef,
        media_ref: str,
        caption: str = "",
        video_metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Send a video using the platform's cached media reference.

        This is the FAST path - the file already lives on the platform's
        servers. No file I/O, no upload, just a reference to existing media.

        Args:
            ref: UserRef identifying the learner and their platform
            media_ref: Telegram file_id, WhatsApp media id, or public URL
            caption: Video caption (truncated to the platform's limit)
            video_metadata: Optional metadata (video_id, title, etc.)
            max_retries: Maximum retry attempts for transient failures

        Returns:
            Dict with success status and message info
        """
        if not media_ref:
            return {
                "success": False,
                "error": "media_ref is required for delivery",
                "suggestion": "Run VideoUploadAgent for this video and platform first.",
            }

        client = self.router.client_for(ref)
        caption = client.truncate_caption(caption)

        # Track delivery attempt
        delivery_id = f"{ref.key}_{datetime.utcnow().timestamp()}"
        self.active_deliveries[ref.key] = {
            "delivery_id": delivery_id,
            "platform": ref.platform.value,
            "media_ref": media_ref,
            "started_at": datetime.utcnow(),
            "status": "sending",
            "metadata": video_metadata
        }

        last_error: Optional[str] = None
        suggestion = ""

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    f"Sending video to {ref} via {ref.platform.value} "
                    f"(attempt {attempt}/{max_retries}, ref: {str(media_ref)[:20]}...)"
                )

                result = await self.router.send_video(ref, media_ref, caption)

                self.active_deliveries[ref.key].update({
                    "status": "delivered",
                    "message_id": result.message_id,
                    "delivered_at": datetime.utcnow(),
                })

                self.delivery_stats["total_sent"] += 1
                if attempt > 1:
                    self.delivery_stats["retried"] += 1

                logger.info(
                    f"Video delivered to {ref} on {ref.platform.value} "
                    f"(message_id: {result.message_id})"
                )

                return {
                    "success": True,
                    "message_id": result.message_id,
                    "platform": ref.platform.value,
                    "chat_id": ref.platform_user_id,
                    "media_ref": media_ref,
                    "attempts": attempt,
                }

            except PermanentMessagingError as exc:
                # Invalid media ref, blocked user, closed 24h window - retrying
                # cannot help, so fail fast with the operator-facing hint.
                last_error = str(exc)
                suggestion = exc.suggestion
                logger.error(f"Permanent delivery failure (no retry): {last_error}")
                break

            except TransientMessagingError as exc:
                last_error = f"{exc} (attempt {attempt}/{max_retries})"
                suggestion = exc.suggestion
                logger.warning(last_error)
                if attempt < max_retries:
                    wait_time = attempt * 2
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)

            except MessagingError as exc:
                last_error = f"{exc} (attempt {attempt}/{max_retries})"
                suggestion = exc.suggestion
                logger.error(last_error)
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 2)

            except Exception as exc:  # noqa: BLE001
                last_error = f"Unexpected error (attempt {attempt}/{max_retries}): {exc}"
                logger.exception(exc)
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 2)

        # All retries failed (or a permanent error broke out early)
        self.active_deliveries[ref.key]["status"] = "failed"
        self.active_deliveries[ref.key]["error"] = last_error
        self.delivery_stats["failed"] += 1

        logger.error(f"Video delivery to {ref} failed: {last_error}")

        return {
            "success": False,
            "error": last_error,
            "platform": ref.platform.value,
            "chat_id": ref.platform_user_id,
            "attempts": attempt,
            "suggestion": suggestion or self._get_error_suggestion(last_error or ""),
        }

    # Backwards-compatible alias for the original Telegram-only entry point
    async def send_video_by_file_id(self, chat_id: str, file_id: str, caption: str = "",
                                    video_metadata: Optional[Dict[str, Any]] = None,
                                    max_retries: int = 3) -> Dict[str, Any]:
        """Deprecated: use send_video_by_media_ref with a UserRef."""
        return await self.send_video_by_media_ref(
            UserRef(Platform.TELEGRAM, str(chat_id)),
            file_id,
            caption=caption,
            video_metadata=video_metadata,
            max_retries=max_retries,
        )

    def _get_error_suggestion(self, error_msg: str) -> str:
        """Provide a helpful suggestion when the platform gave none."""
        error_lower = error_msg.lower()

        if "media" in error_lower or "file_id" in error_lower:
            return "The cached media reference is invalid. Re-upload with VideoUploadAgent."
        elif "24-hour" in error_lower or "131047" in error_lower:
            return "WhatsApp's 24h window has closed. Send an approved template message instead."
        elif "blocked" in error_lower or "not found" in error_lower:
            return "Cannot reach this user. They may have blocked the bot or opted out."
        elif "timed out" in error_lower or "timeout" in error_lower:
            return "Network timeout. Check connectivity and try again."
        return "An unexpected error occurred. Check logs for details."

    async def send_video_by_url(
        self,
        ref: UserRef,
        video_url: str,
        caption: str = "",
        video_metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Send a video by public URL. Both platforms fetch and cache it.

        Telegram returns a reusable file_id in the response; WhatsApp keeps the
        URL as the reference. Prefer an uploaded media reference where possible.
        """
        if not str(video_url).startswith(("http://", "https://")):
            return {
                "success": False,
                "error": "Invalid video URL - must start with http:// or https://"
            }

        return await self.send_video_by_media_ref(
            ref, video_url, caption=caption,
            video_metadata=video_metadata, max_retries=max_retries
        )

    def get_active_delivery(self, ref) -> Optional[Dict[str, Any]]:
        """Get active delivery info for a user (accepts UserRef or key string)"""
        key = ref.key if isinstance(ref, UserRef) else str(ref)
        return self.active_deliveries.get(key)

    def clear_active_delivery(self, ref) -> bool:
        """Clear active delivery state for a user"""
        key = ref.key if isinstance(ref, UserRef) else str(ref)
        if key in self.active_deliveries:
            del self.active_deliveries[key]
            logger.info(f"Cleared active delivery for {key}")
            return True
        return False

    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery metrics"""
        total = self.delivery_stats["total_sent"] + self.delivery_stats["failed"]
        return {
            **self.delivery_stats,
            "active_deliveries": len(self.active_deliveries),
            "success_rate": (self.delivery_stats["total_sent"] / total * 100) if total > 0 else 0
        }

    def get_agent_state(self) -> Dict[str, Any]:
        return {"name": self.name, "status": "active", **self.get_delivery_stats()}
