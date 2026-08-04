"""
Publish videos to messaging platforms (upload once, deliver many).

Run this after adding videos so no learner ever waits on an upload, and to
refresh WhatsApp media ids before they expire (~30 days).

Usage:
    python scripts/publish_videos.py --all
    python scripts/publish_videos.py --video-id 3 --video-id 7
    python scripts/publish_videos.py --all --platform whatsapp
    python scripts/publish_videos.py --status
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from loguru import logger  # noqa: E402

from agents.video_upload_agent import VideoUploadAgent  # noqa: E402
from database.models import Video  # noqa: E402
from database.operations import get_db, init_db, list_media_refs  # noqa: E402
from messaging.base import Platform  # noqa: E402
from messaging.factory import build_router, enabled_platforms  # noqa: E402


def _active_video_ids():
    with get_db() as db:
        return [v.id for v in db.query(Video).filter(Video.is_active == True).all()]  # noqa: E712


def show_status():
    """Print which videos are published to which platforms."""
    init_db()
    platforms = [p.value for p in enabled_platforms()]

    with get_db() as db:
        videos = db.query(Video).order_by(Video.order_index, Video.id).all()

    if not videos:
        print("No videos in the database.")
        return

    print(f"{'ID':<5} {'Title':<40} " + " ".join(f"{p:<12}" for p in platforms))
    print("-" * (46 + 13 * len(platforms)))

    for video in videos:
        refs = {m.platform: m for m in list_media_refs(video.id)}
        cells = []
        for platform in platforms:
            record = refs.get(platform)
            if record:
                cells.append("published")
            elif platform == "telegram" and video.file_id:
                cells.append("legacy id")
            else:
                cells.append("-")
        title = (video.title or "")[:38]
        print(f"{video.id:<5} {title:<40} " + " ".join(f"{c:<12}" for c in cells))


async def publish(video_ids, platform_filter=None):
    init_db()

    router = build_router()
    platforms = [Platform.parse(platform_filter)] if platform_filter else router.platforms
    upload_agent = VideoUploadAgent(router)

    succeeded = failed = 0
    try:
        for video_id in video_ids:
            for platform in platforms:
                result = await upload_agent.ensure_media_ref(video_id, platform)
                if result.get("success"):
                    state = "cached" if result.get("cached") else "uploaded"
                    print(f"  video {video_id} -> {platform.value}: {state}")
                    succeeded += 1
                else:
                    print(f"  video {video_id} -> {platform.value}: FAILED - {result.get('error')}")
                    if result.get("suggestion"):
                        print(f"      hint: {result['suggestion']}")
                    failed += 1
    finally:
        await router.close()

    print(f"\nDone. {succeeded} ok, {failed} failed.")
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description="Publish videos to messaging platforms")
    parser.add_argument("--all", action="store_true", help="Publish every active video")
    parser.add_argument("--video-id", type=int, action="append", default=[],
                        help="Publish a specific video (repeatable)")
    parser.add_argument("--platform", choices=[p.value for p in Platform],
                        help="Limit to one platform (default: every enabled platform)")
    parser.add_argument("--status", action="store_true", help="Show publish status and exit")
    args = parser.parse_args()

    if args.status:
        show_status()
        return 0

    video_ids = args.video_id or (_active_video_ids() if args.all else [])
    if not video_ids:
        parser.error("Pass --all, one or more --video-id, or --status")

    print(f"Publishing {len(video_ids)} video(s)...")
    return asyncio.run(publish(video_ids, args.platform))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("Cancelled by user")
        sys.exit(130)
