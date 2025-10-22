"""
Initialize the database with tables
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.operations import init_db
from loguru import logger


def main():
    """Initialize database"""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.success("Database initialized successfully!")
        
        print("✅ Database tables created successfully!")
        print("\nYou can now:")
        print("1. Run 'python scripts/load_documents.py' to load company documents")
        print("2. Run 'python scripts/add_sample_videos.py' to add sample videos")
        print("3. Run 'python main.py' to start the bot")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
