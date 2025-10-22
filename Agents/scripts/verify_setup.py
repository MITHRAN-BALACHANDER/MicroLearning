"""
Verify project setup and configuration
"""
import sys
import os
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_file_exists(filepath: str) -> Tuple[bool, str]:
    """Check if a file exists"""
    path = Path(filepath)
    if path.exists():
        return True, f"✓ {filepath}"
    else:
        return False, f"✗ {filepath} - MISSING"


def check_directory_exists(dirpath: str) -> Tuple[bool, str]:
    """Check if a directory exists"""
    path = Path(dirpath)
    if path.exists() and path.is_dir():
        return True, f"✓ {dirpath}/"
    else:
        return False, f"✗ {dirpath}/ - MISSING"


def check_env_variable(var_name: str) -> Tuple[bool, str]:
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if value and value != f"your_{var_name.lower()}_here":
        return True, f"✓ {var_name} is set"
    else:
        return False, f"✗ {var_name} - NOT SET or using default"


def verify_setup():
    """Verify complete project setup"""
    print("=" * 60)
    print("MicroLearning Bot - Setup Verification")
    print("=" * 60)
    print()
    
    all_checks = []
    
    # Check required files
    print("📁 Checking Project Files...")
    print("-" * 60)
    required_files = [
        "main.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
        "QUICKSTART.md",
        "agents/video_agent.py",
        "agents/question_agent.py",
        "agents/rag_agent.py",
        "agents/orchestrator.py",
        "database/models.py",
        "database/operations.py",
        "config/settings.py",
        "scripts/init_db.py",
        "scripts/load_documents.py",
        "scripts/add_sample_videos.py",
    ]
    
    for filepath in required_files:
        result, message = check_file_exists(filepath)
        all_checks.append(result)
        print(message)
    
    print()
    
    # Check required directories
    print("📂 Checking Directories...")
    print("-" * 60)
    required_dirs = [
        "agents",
        "database",
        "config",
        "scripts",
        "utils",
        "data",
        "data/documents",
        "logs",
    ]
    
    for dirpath in required_dirs:
        result, message = check_directory_exists(dirpath)
        all_checks.append(result)
        print(message)
    
    print()
    
    # Check .env file
    print("⚙️  Checking Environment Configuration...")
    print("-" * 60)
    
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file exists")
        
        # Try to load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        env_vars = [
            "TELEGRAM_BOT_TOKEN",
            "OPENAI_API_KEY",
            "DATABASE_URL",
        ]
        
        for var in env_vars:
            result, message = check_env_variable(var)
            all_checks.append(result)
            print(message)
    else:
        print("✗ .env file NOT FOUND")
        print("  → Copy .env.example to .env and configure it")
        all_checks.append(False)
    
    print()
    
    # Check Python packages
    print("📦 Checking Python Packages...")
    print("-" * 60)
    
    required_packages = [
        "telegram",
        "openai",
        "sqlalchemy",
        "chromadb",
        "sentence_transformers",
        "loguru",
        "apscheduler",
        "dotenv",
    ]
    
    for package in required_packages:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print(f"✓ {package}")
            all_checks.append(True)
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            all_checks.append(False)
    
    print()
    
    # Check sample data
    print("📄 Checking Sample Data...")
    print("-" * 60)
    
    doc_files = list(Path("data/documents").glob("*.txt"))
    if doc_files:
        print(f"✓ Found {len(doc_files)} sample document(s)")
        for doc in doc_files:
            print(f"  • {doc.name}")
    else:
        print("⚠ No documents found in data/documents/")
        print("  → Sample documents should be present")
    
    print()
    
    # Database check
    print("🗄️  Checking Database...")
    print("-" * 60)
    
    try:
        from database.operations import get_db
        from database.models import User, Video, Document
        
        with get_db() as db:
            user_count = db.query(User).count()
            video_count = db.query(Video).count()
            doc_count = db.query(Document).count()
            
            print(f"✓ Database accessible")
            print(f"  • Users: {user_count}")
            print(f"  • Videos: {video_count}")
            print(f"  • Documents: {doc_count}")
            
            if video_count == 0:
                print("  ⚠ No videos in database")
                print("    → Run: python scripts/add_sample_videos.py")
            
            if doc_count == 0:
                print("  ⚠ No documents indexed")
                print("    → Run: python scripts/load_documents.py")
            
            all_checks.append(True)
    except Exception as e:
        print(f"✗ Database error: {str(e)}")
        print("  → Run: python scripts/init_db.py")
        all_checks.append(False)
    
    print()
    print("=" * 60)
    
    # Summary
    passed = sum(all_checks)
    total = len(all_checks)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Setup Verification: {passed}/{total} checks passed ({percentage:.1f}%)")
    print("=" * 60)
    print()
    
    if all(all_checks):
        print("✅ All checks passed! Your setup is complete.")
        print("\nNext steps:")
        print("1. Make sure .env has your actual API keys")
        print("2. Run: python main.py")
        print("3. Open Telegram and send /start to your bot")
    else:
        print("⚠️  Some checks failed. Please review the issues above.")
        print("\nCommon fixes:")
        print("1. Install packages: pip install -r requirements.txt")
        print("2. Configure .env: copy .env.example to .env and edit")
        print("3. Initialize database: python scripts/init_db.py")
        print("4. Add sample data:")
        print("   - python scripts/add_sample_videos.py")
        print("   - python scripts/load_documents.py")
    
    print()


if __name__ == "__main__":
    verify_setup()
