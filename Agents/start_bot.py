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
    GEMINI_API_KEY,
    DATABASE_URL,
    VIDEOS_DIR,
    DOCUMENTS_DIR,
    LOGS_DIR
)
from database.operations import get_db
from database.models import Video, Question, User


def check_environment():
    """Check all required environment variables"""
    print("=" * 60)
    print("ENVIRONMENT VALIDATION")
    print("=" * 60)
    
    required_vars = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "GEMINI_API_KEY": GEMINI_API_KEY
    }
    
    missing = []
    for var_name, var_value in required_vars.items():
        if not var_value:
            print(f"❌ {var_name}: MISSING")
            missing.append(var_name)
        else:
            masked = var_value[:10] + "..." if len(var_value) > 10 else var_value
            print(f"✅ {var_name}: {masked}")
    
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
    """Check video files"""
    print("\n" + "=" * 60)
    print("VIDEO FILES VALIDATION")
    print("=" * 60)
    
    try:
        with get_db() as db:
            videos = db.query(Video).filter(Video.is_active == True).all()
            
            if not videos:
                print("⚠️  No videos in database")
                print("   Run: python scripts/reset_videos_from_folder.py")
                return False
            
            missing_files = []
            for video in videos:
                if not os.path.exists(video.file_path):
                    missing_files.append(video.title)
            
            print(f"Total videos: {len(videos)}")
            if missing_files:
                print(f"❌ Missing video files: {len(missing_files)}")
                for title in missing_files[:5]:  # Show first 5
                    print(f"   - {title}")
                return False
            else:
                print(f"✅ All video files present")
            
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
