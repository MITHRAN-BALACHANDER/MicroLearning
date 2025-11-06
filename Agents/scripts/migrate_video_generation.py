"""
Database migration script to add video_generation_jobs table
Run this script to update your database with the new video generation functionality
"""
from database.operations import SessionLocal, init_db
from database.models import Base, VideoGenerationJob
from sqlalchemy import create_engine
from config.settings import DATABASE_URL
import sys

def migrate_database():
    """Add video generation jobs table to database"""
    print("=" * 60)
    print("DATABASE MIGRATION: Adding Video Generation Jobs Table")
    print("=" * 60)
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Create all tables (will only create missing ones)
        print("\n📊 Creating tables...")
        Base.metadata.create_all(engine)
        
        print("✅ Database migration completed successfully!")
        print("\nNew table added:")
        print("  - video_generation_jobs")
        print("\nYou can now use the AI video generation feature!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
