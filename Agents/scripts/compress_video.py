"""
Re-encode a video to fit a platform's size cap.

WhatsApp's Cloud API refuses anything over 16 MB, which is well under
Telegram's 50 MB, so a lesson that delivers fine on one channel can be
undeliverable on the other. This shrinks it.

Encoding uses the ffmpeg binary that ships with imageio-ffmpeg (a moviepy
dependency), so no system ffmpeg install is required.


    python scripts/compress_video.py --video 16 --target-mb 12
    python scripts/compress_video.py --in a.mp4 --out b.mp4 --target-mb 12
"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import av  # noqa: E402

AUDIO_KBPS = 64


def probe(path: str) -> dict:
    with av.open(path) as container:
        video = next((s for s in container.streams if s.type == "video"), None)
        audio = next((s for s in container.streams if s.type == "audio"), None)
        if video is None:
            raise SystemExit(f"No video stream in {path}")
        return {
            "duration": container.duration / av.time_base,
            "width": video.codec_context.width,
            "height": video.codec_context.height,
            "rate": video.average_rate,
            "has_audio": audio is not None,
            "size_mb": os.path.getsize(path) / 1048576,
        }


def _ffmpeg() -> str:
    """
    Path to a real ffmpeg binary.

    PyAV bundles FFmpeg's *libraries*, not its CLI, and hand-rolling the
    transcode against those means owning muxer details (AAC priming packets
    carry a negative pts that the mp4 muxer rejects, among others). imageio-ffmpeg
    ships the actual binary and arrives with moviepy, which is already a
    dependency - so use it, and fall back to anything on PATH.
    """
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def transcode(src: str, dst: str, target_mb: float, max_height: int = 0) -> None:
    """
    Two-pass re-encode at a bitrate chosen to land near `target_mb`.

    Two passes rather than one because the point is clearing a hard cap: a
    single pass overshoots or undershoots by a wide margin on content whose
    complexity varies, and "probably under 16 MB" is not good enough when the
    platform rejects the upload outright.
    """
    import subprocess

    info = probe(src)
    duration = info["duration"]

    total_kbps = (target_mb * 8 * 1024) / duration
    video_kbps = max(120, int(total_kbps - (AUDIO_KBPS if info["has_audio"] else 0)))

    scale = []
    if max_height and info["height"] > max_height:
        scale = ["-vf", f"scale=-2:{max_height}"]

    print(f"  source : {info['size_mb']:.1f} MB, {info['width']}x{info['height']}, "
          f"{duration:.0f}s")
    print(f"  target : {target_mb:.0f} MB -> video {video_kbps} kbps"
          f"{f', scaled to height {max_height}' if scale else ''}")

    exe = _ffmpeg()
    common = [
        exe, "-nostdin", "-y", "-i", src,
        # Animation: flat colour and hard edges, so the tuning buys real
        # quality at this bitrate.
        "-c:v", "libx264", "-b:v", f"{video_kbps}k",
        "-tune", "animation", "-preset", "medium", "-profile:v", "high",
        "-pix_fmt", "yuv420p", *scale,
    ]
    passlog = str(Path(dst).with_suffix("")) + "_2pass"

    started = time.time()
    print("  pass 1 ...")
    subprocess.run(
        common + ["-pass", "1", "-passlogfile", passlog, "-an",
                  "-f", "mp4", os.devnull],
        check=True, capture_output=True,
    )
    print("  pass 2 ...")
    subprocess.run(
        common + ["-pass", "2", "-passlogfile", passlog,
                  "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k",
                  # Streaming-friendly: the player can start before the whole
                  # file arrives, which matters on a phone on mobile data.
                  "-movflags", "+faststart", dst],
        check=True, capture_output=True,
    )

    for leftover in Path(dst).parent.glob(Path(passlog).name + "*"):
        leftover.unlink(missing_ok=True)

    size_mb = os.path.getsize(dst) / 1048576
    print(f"  result : {size_mb:.1f} MB in {time.time() - started:.0f}s "
          f"({info['size_mb'] / size_mb:.1f}x smaller)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=int, help="video id in the database")
    parser.add_argument("--in", dest="source", help="input file (instead of --video)")
    parser.add_argument("--out", dest="dest", help="output file")
    parser.add_argument("--target-mb", type=float, default=12.0)
    parser.add_argument("--max-height", type=int, default=0,
                        help="scale down to at most this height (0 = keep)")
    parser.add_argument("--replace", action="store_true",
                        help="point the database row at the compressed file")
    args = parser.parse_args()

    if args.video:
        from database.models import Video
        from database.operations import get_db

        with get_db() as db:
            video = db.query(Video).filter(Video.id == args.video).first()
            if not video:
                raise SystemExit(f"No video with id {args.video}")
            source = video.file_path
            title = video.title
        print(f"video {args.video}: {title}")
    else:
        if not args.source:
            raise SystemExit("Pass --video or --in")
        source = args.source

    if not os.path.exists(source):
        raise SystemExit(f"File not found: {source}")

    dest = args.dest or str(Path(source).with_name(Path(source).stem + "_compressed.mp4"))
    transcode(source, dest, args.target_mb, args.max_height)

    if args.video and args.replace:
        from database.models import Video
        from database.operations import get_db

        with get_db() as db:
            video = db.query(Video).filter(Video.id == args.video).first()
            video.file_path = dest
            video.file_id = dest
            # Any cached per-platform handle points at the old, larger file.
            for media in list(video.media_refs):
                media.is_active = False
            db.commit()
        print(f"  database: video {args.video} now points at the compressed file")
        print("  (cached media refs retired - it will re-upload on next delivery)")


if __name__ == "__main__":
    main()
