"""
Database migration script to add role and category fields
"""
from sqlalchemy import create_engine, text
from config.settings import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_role_columns():
    """Add role column to users table and category column to videos table"""
    engine = create_engine(DATABASE_URL)
    
    logger.info("Adding role and category columns...")
    
    with engine.connect() as conn:
        # Add role column to users table
        try:
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'learner';
            """))
            conn.commit()
            logger.info("✓ Added role column to users table")
        except Exception as e:
            logger.warning(f"Role column may already exist: {e}")
        
        # Add category column to videos table
        try:
            conn.execute(text("""
                ALTER TABLE videos ADD COLUMN category TEXT DEFAULT 'general';
            """))
            conn.commit()
            logger.info("✓ Added category column to videos table")
        except Exception as e:
            logger.warning(f"Category column may already exist: {e}")
        
        # Update existing users to have default role
        try:
            conn.execute(text("""
                UPDATE users SET role = 'learner' WHERE role IS NULL;
            """))
            conn.commit()
            logger.info("✓ Updated existing users with default role")
        except Exception as e:
            logger.warning(f"Could not update users: {e}")
        
        # Update existing videos to have default category
        try:
            conn.execute(text("""
                UPDATE videos SET category = 'general' WHERE category IS NULL;
            """))
            conn.commit()
            logger.info("✓ Updated existing videos with default category")
        except Exception as e:
            logger.warning(f"Could not update videos: {e}")
        
        # Create indexes for new columns
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            """))
            conn.commit()
            logger.info("✓ Created index on users.role")
        except Exception as e:
            logger.warning(f"Index may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_videos_category ON videos(category);
            """))
            conn.commit()
            logger.info("✓ Created index on videos.category")
        except Exception as e:
            logger.warning(f"Index may already exist: {e}")
    
    logger.info("✓ Migration complete!")


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("Running Database Migration")
    logger.info("="*60)
    add_role_columns()
    logger.info("="*60)
