"""
Production startup script with pre-flight checks
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ENABLED,
    WHATSAPP_ENABLED,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_VERIFY_TOKEN,
    WHATSAPP_APP_SECRET,
    WHATSAPP_WEBHOOK_PATH,
    WEBHOOK_PORT,
    ENABLED_PLATFORMS,
    GEMINI_API_KEY,
    DATABASE_URL,
    VIDEOS_DIR,
    DOCUMENTS_DIR,
    LOGS_DIR
)
from database.operations import get_db, get_media_ref, init_db
from database.models import Video, Question, User


def _mask(value):
    return value[:10] + "..." if value and len(value) > 10 else (value or "")


def check_environment():
    """Check all required environment variables for the enabled platforms"""
    print("=" * 60)
    print("ENVIRONMENT VALIDATION")
    print("=" * 60)
    print(f"MESSAGING_PLATFORM -> {', '.join(ENABLED_PLATFORMS)}")
    print()

    required_vars = {"GEMINI_API_KEY": GEMINI_API_KEY}

    if TELEGRAM_ENABLED:
        required_vars["TELEGRAM_BOT_TOKEN"] = TELEGRAM_BOT_TOKEN

    if WHATSAPP_ENABLED:
        required_vars["WHATSAPP_ACCESS_TOKEN"] = WHATSAPP_ACCESS_TOKEN
        required_vars["WHATSAPP_PHONE_NUMBER_ID"] = WHATSAPP_PHONE_NUMBER_ID
        required_vars["WHATSAPP_VERIFY_TOKEN"] = WHATSAPP_VERIFY_TOKEN

    missing = []
    for var_name, var_value in required_vars.items():
        if not var_value:
            print(f"❌ {var_name}: MISSING")
            missing.append(var_name)
        else:
            print(f"✅ {var_name}: {_mask(var_value)}")

    if WHATSAPP_ENABLED:
        if WHATSAPP_APP_SECRET:
            print(f"✅ WHATSAPP_APP_SECRET: {_mask(WHATSAPP_APP_SECRET)}")
        else:
            print("⚠️  WHATSAPP_APP_SECRET: not set - webhook signatures will NOT be verified")
        print(f"   Webhook path: {WHATSAPP_WEBHOOK_PATH} (port {WEBHOOK_PORT})")
        print("   Meta must be able to reach this over public HTTPS")

    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        print("Please set them in your .env file")
        return False

    print("\n✅ All environment variables present")
    return True


def check_directories():
    """Check all required directories exist"""
    print("\n" + "=" * 60)
    print("DIRECTORY VALIDATION")
    print("=" * 60)
    
    directories = {
        "Videos": VIDEOS_DIR,
        "Documents": DOCUMENTS_DIR,
        "Logs": LOGS_DIR
    }
    
    all_exist = True
    for dir_name, dir_path in directories.items():
        if dir_path.exists():
            print(f"✅ {dir_name}: {dir_path}")
        else:
            print(f"⚠️  {dir_name}: {dir_path} (creating...)")
            dir_path.mkdir(parents=True, exist_ok=True)
            all_exist = False
    
    return True


def check_database():
    """Check database connectivity and data"""
    print("\n" + "=" * 60)
    print("DATABASE VALIDATION")
    print("=" * 60)

    try:
        # Create any missing tables and apply additive column upgrades BEFORE
        # querying, otherwise an older database fails on the newer model.
        applied = init_db()
        if applied:
            print(f"✅ Schema upgraded: {', '.join(applied)}")

        with get_db() as db:
            # Check tables
            user_count = db.query(User).count()
            video_count = db.query(Video).count()
            question_count = db.query(Question).count()
            
            # Check for videos without questions
            videos = db.query(Video).filter(Video.is_active == True).all()
            videos_without_questions = 0
            for video in videos:
                q_count = db.query(Question).filter(
                    Question.video_id == video.id,
                    Question.is_active == True
                ).count()
                if q_count == 0:
                    videos_without_questions += 1
            
            print(f"✅ Database: {DATABASE_URL}")
            print(f"   Users: {user_count}")
            print(f"   Videos: {video_count}")
            print(f"   Questions: {question_count}")
            
            if videos_without_questions > 0:
                print(f"   ⚠️  Videos without questions: {videos_without_questions}")
                print(f"      Run: python scripts/generate_all_questions.py")
            else:
                print(f"   ✅ All videos have questions")
            
            return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def check_videos():
    """
    Check that videos can actually be delivered on each enabled platform.

    A video is deliverable if it already has a cached media reference for that
    platform. If not, it needs its local source file so it can be uploaded once.
    A missing local file therefore only blocks platforms the video has not been
    published to yet - it does not block delivery where a cached handle exists.
    """
    print("\n" + "=" * 60)
    print("VIDEO DELIVERY VALIDATION")
    print("=" * 60)

    # WhatsApp rejects anything over 16 MB
    whatsapp_limit = 16 * 1024 * 1024

    try:
        with get_db() as db:
            videos = db.query(Video).filter(Video.is_active == True).all()

            if not videos:
                print("⚠️  No videos in database")
                print("   Run: python scripts/reset_videos_from_folder.py")
                return False

            print(f"Total active videos: {len(videos)}\n")

            any_deliverable = False
            for platform in ENABLED_PLATFORMS:
                published, uploadable, blocked, oversized = [], [], [], []

                for video in videos:
                    if get_media_ref(video.id, platform):
                        published.append(video.title)
                        continue

                    path = video.file_path
                    if path and os.path.exists(path):
                        if platform == "whatsapp" and os.path.getsize(path) > whatsapp_limit:
                            oversized.append((video.title, os.path.getsize(path)))
                        else:
                            uploadable.append(video.title)
                    else:
                        blocked.append(video.title)

                deliverable = len(published) + len(uploadable)
                any_deliverable = any_deliverable or deliverable > 0

                print(f"{platform.upper()}:")
                print(f"   ✅ Already published: {len(published)}")
                if uploadable:
                    print(f"   ⬆️  Ready to upload:  {len(uploadable)}")
                    print(f"      Pre-publish with: python scripts/publish_videos.py --all --platform {platform}")
                for title, size in oversized:
                    print(f"   ❌ Too large for WhatsApp ({size / 1024 / 1024:.1f} MB > 16 MB): {title[:50]}")
                for title in blocked:
                    print(f"   ❌ No cached media and source file missing: {title[:50]}")
                print(f"   -> {deliverable}/{len(videos)} deliverable\n")

            if not any_deliverable:
                print("❌ No videos can be delivered on any enabled platform")
                return False

            return True
    except Exception as e:
        print(f"❌ Video check error: {e}")
        return False


def main():
    """Run all pre-flight checks"""
    print("\n")
    print("🚀" * 30)
    print("MICROLEARNING BOT - PRODUCTION STARTUP")
    print("🚀" * 30)
    print()
    
    checks = [
        ("Environment Variables", check_environment),
        ("Directories", check_directories),
        ("Database", check_database),
        ("Video Files", check_videos)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - READY TO START")
        print("=" * 60)
        print("\nStarting bot...")
        print()
        
        # Import and run bot
        from main import MicroLearningBot
        bot = MicroLearningBot()
        bot.run()
    else:
        print("❌ SOME CHECKS FAILED - PLEASE FIX ISSUES ABOVE")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Startup cancelled by user")
    except Exception as e:
        print(f"\n❌ Startup error: {e}")
        sys.exit(1)
