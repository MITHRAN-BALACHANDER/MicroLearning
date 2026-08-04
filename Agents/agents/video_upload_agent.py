"""
Video Upload Agent - uploads a video ONCE per platform and caches the handle.

This is the write half of the upload-once / deliver-many design:

    VideoUploadAgent  -> uploads the file, stores the platform media reference
    VideoDeliveryAgent -> sends to N users using that cached reference

Each platform returns its own opaque handle:
  - Telegram: file_id, obtained by posting the video to a staging chat once
  - WhatsApp: media id from the Cloud API /media endpoint (expires ~30 days)

Uploads are never triggered by a learner's request path unless
AUTO_UPLOAD_MEDIA is on, and even then only once per video per platform.
"""
import asyncio
import os
from typing import Any, Dict, List, Optional

from loguru import logger

from config.settings import TELEGRAM_UPLOAD_STAGING_CHAT_ID
from database.operations import get_video_by_id, set_media_ref, get_media_ref
from messaging.base import MessagingError, Platform, TransientMessagingError

# WhatsApp media ids stop working after 30 days; refresh a little early.
WHATSAPP_MEDIA_TTL_DAYS = 28


class VideoUploadAgent:
    """Uploads video files to messaging platforms and caches the media handles."""

    def __init__(self, router):
        self.router = router
        self.name = "VideoUploadAgent"
        self.description = "Uploads videos once per platform and caches media references"
        self.upload_stats: Dict[str, int] = {"uploaded": 0, "failed": 0, "cached_hits": 0}
        # Guards against two concurrent requests uploading the same video twice
        self._locks: Dict[str, asyncio.Lock] = {}
        logger.info(f"Initialized {self.name}")

    def _lock_for(self, video_id: int, platform: Platform) -> asyncio.Lock:
        key = f"{platform.value}:{video_id}"
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def ensure_media_ref(self, video_id: int, platform, *,
                               max_retries: int = 3) -> Dict[str, Any]:
        """
        Return a usable media reference for (video, platform), uploading only
        if one is not already cached.
        """
        platform = Platform.parse(platform)

        cached = get_media_ref(video_id, platform.value)
        if cached:
            self.upload_stats["cached_hits"] += 1
            return {"success": True, "media_ref": cached, "cached": True, "platform": platform.value}

        async with self._lock_for(video_id, platform):
            # Another coroutine may have uploaded it while we waited
            cached = get_media_ref(video_id, platform.value)
            if cached:
                self.upload_stats["cached_hits"] += 1
                return {"success": True, "media_ref": cached, "cached": True, "platform": platform.value}

            return await self.upload_video(video_id, platform, max_retries=max_retries)

    async def upload_video(self, video_id: int, platform, *,
                           max_retries: int = 3) -> Dict[str, Any]:
        """Upload a video's local file to a platform and cache the handle."""
        platform = Platform.parse(platform)

        video = get_video_by_id(video_id)
        if not video:
            return {"success": False, "error": f"Video {video_id} not found", "platform": platform.value}

        file_path = video.file_path
        if not file_path or not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"No local file for video {video_id} ({file_path or 'no path stored'})",
                "suggestion": "Set videos.file_path to the source file, or store a public URL as the media reference.",
                "platform": platform.value,
            }

        file_size = os.path.getsize(file_path)
        logger.info(
            f"Uploading video {video_id} ({file_size / 1024 / 1024:.1f} MB) to {platform.value}"
        )

        last_error: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                result = await self.router.upload_video(
                    platform,
                    file_path,
                    staging_chat_id=TELEGRAM_UPLOAD_STAGING_CHAT_ID,
                )

                set_media_ref(
                    video_id=video_id,
                    platform=platform.value,
                    media_ref=result.media_ref,
                    file_size_bytes=file_size,
                    ttl_days=WHATSAPP_MEDIA_TTL_DAYS if platform is Platform.WHATSAPP else None,
                )

                self.upload_stats["uploaded"] += 1
                logger.info(
                    f"Video {video_id} uploaded to {platform.value} "
                    f"(ref: {str(result.media_ref)[:24]}..., attempt {attempt})"
                )
                return {
                    "success": True,
                    "media_ref": result.media_ref,
                    "cached": False,
                    "platform": platform.value,
                    "file_size_mb": round(file_size / 1024 / 1024, 2),
                    "attempts": attempt,
                }

            except TransientMessagingError as exc:
                last_error = exc
                logger.warning(
                    f"Transient upload failure for video {video_id} on {platform.value} "
                    f"(attempt {attempt}/{max_retries}): {exc}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 5)

            except MessagingError as exc:
                self.upload_stats["failed"] += 1
                logger.error(f"Upload rejected for video {video_id} on {platform.value}: {exc}")
                return {
                    "success": False,
                    "error": str(exc),
                    "suggestion": exc.suggestion,
                    "platform": platform.value,
                }

            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.exception(f"Unexpected upload error for video {video_id}")
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 5)

        self.upload_stats["failed"] += 1
        return {
            "success": False,
            "error": f"Upload failed after {max_retries} attempts: {last_error}",
            "platform": platform.value,
        }

    async def upload_to_all_platforms(self, video_id: int) -> Dict[str, Any]:
        """Publish a video to every enabled platform."""
        results = {}
        for platform in self.router.platforms:
            results[platform.value] = await self.ensure_media_ref(video_id, platform)
        return {
            "video_id": video_id,
            "results": results,
            "success": any(r.get("success") for r in results.values()),
        }

    async def backfill(self, video_ids: List[int]) -> Dict[str, Any]:
        """Pre-upload a batch of videos so no learner ever waits for an upload."""
        summary = {"total": len(video_ids), "succeeded": 0, "failed": 0, "details": {}}
        for video_id in video_ids:
            result = await self.upload_to_all_platforms(video_id)
            summary["details"][video_id] = result["results"]
            if result["success"]:
                summary["succeeded"] += 1
            else:
                summary["failed"] += 1
        return summary

    def get_agent_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            **self.upload_stats,
            "status": "active",
        }
