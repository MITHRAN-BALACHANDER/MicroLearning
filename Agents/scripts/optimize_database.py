"""
Database Performance Optimization Script
Adds indexes and optimizations for analytics queries
"""
from sqlalchemy import create_engine, Index, text
from database.models import Base, User, Video, VideoProgress, Question, QuizAttempt, Document, UserSession
from config.settings import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_performance_indexes():
    """Add indexes to improve analytics query performance"""
    engine = create_engine(DATABASE_URL)
    
    logger.info("Creating performance indexes...")
    
    with engine.connect() as conn:
        # User indexes
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_last_active 
                ON users(last_active DESC);
            """))
            logger.info("✓ Created index on users.last_active")
        except Exception as e:
            logger.warning(f"Index idx_users_last_active may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_created_at 
                ON users(created_at DESC);
            """))
            logger.info("✓ Created index on users.created_at")
        except Exception as e:
            logger.warning(f"Index idx_users_created_at may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_is_active 
                ON users(is_active);
            """))
            logger.info("✓ Created index on users.is_active")
        except Exception as e:
            logger.warning(f"Index idx_users_is_active may already exist: {e}")
        
        # Video indexes
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_videos_is_active 
                ON videos(is_active);
            """))
            logger.info("✓ Created index on videos.is_active")
        except Exception as e:
            logger.warning(f"Index idx_videos_is_active may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_videos_difficulty 
                ON videos(difficulty_level);
            """))
            logger.info("✓ Created index on videos.difficulty_level")
        except Exception as e:
            logger.warning(f"Index idx_videos_difficulty may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_videos_created_at 
                ON videos(created_at DESC);
            """))
            logger.info("✓ Created index on videos.created_at")
        except Exception as e:
            logger.warning(f"Index idx_videos_created_at may already exist: {e}")
        
        # VideoProgress indexes
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_video_progress_user_video 
                ON video_progress(user_id, video_id);
            """))
            logger.info("✓ Created composite index on video_progress(user_id, video_id)")
        except Exception as e:
            logger.warning(f"Index idx_video_progress_user_video may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_video_progress_completed 
                ON video_progress(completed);
            """))
            logger.info("✓ Created index on video_progress.completed")
        except Exception as e:
            logger.warning(f"Index idx_video_progress_completed may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_video_progress_watched_at 
                ON video_progress(watched_at DESC);
            """))
            logger.info("✓ Created index on video_progress.watched_at")
        except Exception as e:
            logger.warning(f"Index idx_video_progress_watched_at may already exist: {e}")
        
        # Question indexes
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_questions_video_id 
                ON questions(video_id);
            """))
            logger.info("✓ Created index on questions.video_id")
        except Exception as e:
            logger.warning(f"Index idx_questions_video_id may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_questions_is_active 
                ON questions(is_active);
            """))
            logger.info("✓ Created index on questions.is_active")
        except Exception as e:
            logger.warning(f"Index idx_questions_is_active may already exist: {e}")
        
        # QuizAttempt indexes
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_id 
                ON quiz_attempts(user_id);
            """))
            logger.info("✓ Created index on quiz_attempts.user_id")
        except Exception as e:
            logger.warning(f"Index idx_quiz_attempts_user_id may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_quiz_attempts_question_id 
                ON quiz_attempts(question_id);
            """))
            logger.info("✓ Created index on quiz_attempts.question_id")
        except Exception as e:
            logger.warning(f"Index idx_quiz_attempts_question_id may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_quiz_attempts_attempted_at 
                ON quiz_attempts(attempted_at DESC);
            """))
            logger.info("✓ Created index on quiz_attempts.attempted_at")
        except Exception as e:
            logger.warning(f"Index idx_quiz_attempts_attempted_at may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_quiz_attempts_rating 
                ON quiz_attempts(rating);
            """))
            logger.info("✓ Created index on quiz_attempts.rating")
        except Exception as e:
            logger.warning(f"Index idx_quiz_attempts_rating may already exist: {e}")
        
        # Document indexes
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_documents_is_active 
                ON documents(is_active);
            """))
            logger.info("✓ Created index on documents.is_active")
        except Exception as e:
            logger.warning(f"Index idx_documents_is_active may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_documents_doc_type 
                ON documents(doc_type);
            """))
            logger.info("✓ Created index on documents.doc_type")
        except Exception as e:
            logger.warning(f"Index idx_documents_doc_type may already exist: {e}")
        
        # UserSession indexes
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id 
                ON user_sessions(user_id);
            """))
            logger.info("✓ Created index on user_sessions.user_id")
        except Exception as e:
            logger.warning(f"Index idx_user_sessions_user_id may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active 
                ON user_sessions(is_active);
            """))
            logger.info("✓ Created index on user_sessions.is_active")
        except Exception as e:
            logger.warning(f"Index idx_user_sessions_is_active may already exist: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_sessions_started_at 
                ON user_sessions(started_at DESC);
            """))
            logger.info("✓ Created index on user_sessions.started_at")
        except Exception as e:
            logger.warning(f"Index idx_user_sessions_started_at may already exist: {e}")
        
        conn.commit()
    
    logger.info("✓ All performance indexes created successfully!")


def analyze_tables():
    """Run ANALYZE to update statistics for query optimizer"""
    engine = create_engine(DATABASE_URL)
    
    logger.info("Running ANALYZE on tables...")
    
    with engine.connect() as conn:
        tables = [
            'users', 'videos', 'video_progress', 'questions', 
            'quiz_attempts', 'documents', 'user_sessions'
        ]
        
        for table in tables:
            try:
                conn.execute(text(f"ANALYZE {table};"))
                logger.info(f"✓ Analyzed {table}")
            except Exception as e:
                logger.warning(f"Could not analyze {table}: {e}")
        
        conn.commit()
    
    logger.info("✓ Table analysis complete!")


def vacuum_database():
    """Run VACUUM to reclaim space and optimize"""
    engine = create_engine(DATABASE_URL)
    
    logger.info("Running VACUUM...")
    
    # VACUUM can't run inside a transaction, so we need raw connection
    with engine.raw_connection() as conn:
        conn.set_isolation_level(0)  # AUTOCOMMIT mode
        cursor = conn.cursor()
        try:
            cursor.execute("VACUUM;")
            logger.info("✓ VACUUM complete!")
        except Exception as e:
            logger.warning(f"Could not run VACUUM: {e}")
        finally:
            cursor.close()


def optimize_database():
    """Run all optimization operations"""
    logger.info("="*60)
    logger.info("Starting Database Optimization")
    logger.info("="*60)
    
    add_performance_indexes()
    analyze_tables()
    
    try:
        vacuum_database()
    except Exception as e:
        logger.warning(f"VACUUM failed (this is normal for some SQLite versions): {e}")
    
    logger.info("="*60)
    logger.info("Database Optimization Complete!")
    logger.info("="*60)


if __name__ == '__main__':
    optimize_database()
