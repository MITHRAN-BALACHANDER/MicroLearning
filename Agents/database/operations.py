"""
Database operations and utility functions
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import List, Optional
from datetime import datetime, timedelta
import json

from database.models import (
    Base, User, Video, VideoMedia, VideoProgress, Question, QuizAttempt, Document, UserSession
)
from database.migrations import ensure_schema
from config.settings import DATABASE_URL


# Create engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database tables and apply additive schema upgrades.

    Returns the list of columns added, so callers can report the upgrade.
    """
    Base.metadata.create_all(bind=engine)
    return ensure_schema(engine)


@contextmanager
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# User Operations
def get_or_create_user(telegram_id: str, username: str = None, first_name: str = None,
                       last_name: str = None, platform: str = "telegram",
                       platform_user_id: str = None, touch_inbound: bool = False) -> User:
    """
    Get or create a user.

    `telegram_id` is the platform-qualified key (bare chat id for Telegram,
    "whatsapp:<wa_id>" for WhatsApp) - see messaging.UserRef.key.
    """
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        now = datetime.utcnow()

        if not user:
            user = User(
                telegram_id=telegram_id,
                platform=platform,
                platform_user_id=platform_user_id or telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                last_inbound_at=now if touch_inbound else None
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update last active and backfill any profile details we now know
            user.last_active = now
            if touch_inbound:
                user.last_inbound_at = now
            if not user.platform:
                user.platform = platform
            if not user.platform_user_id:
                user.platform_user_id = platform_user_id or telegram_id
            if username and not user.username:
                user.username = username
            if first_name and not user.first_name:
                user.first_name = first_name
            if last_name and not user.last_name:
                user.last_name = last_name
            db.commit()
            db.refresh(user)
        return user


def get_user_by_telegram_id(telegram_id: str) -> Optional[User]:
    """Get user by platform-qualified key (kept for backwards compatibility)"""
    with get_db() as db:
        return db.query(User).filter(User.telegram_id == telegram_id).first()


def get_user_by_ref(ref) -> Optional[User]:
    """Get a user from a messaging.UserRef"""
    return get_user_by_telegram_id(ref.key)


def get_or_create_user_from_ref(ref, username: str = None, first_name: str = None,
                               last_name: str = None, touch_inbound: bool = True) -> User:
    """Get or create a user from a messaging.UserRef"""
    return get_or_create_user(
        telegram_id=ref.key,
        username=username,
        first_name=first_name,
        last_name=last_name,
        platform=ref.platform.value,
        platform_user_id=ref.platform_user_id,
        touch_inbound=touch_inbound
    )


def touch_user_inbound(telegram_id: str):
    """Record that the user just messaged us (starts WhatsApp's 24h window)"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            now = datetime.utcnow()
            user.last_inbound_at = now
            user.last_active = now
            db.commit()


def get_active_users(platform: str = None) -> List[User]:
    """Get active users, optionally filtered to one platform"""
    with get_db() as db:
        query = db.query(User).filter(User.is_active == True)
        if platform:
            query = query.filter(User.platform == platform)
        return query.all()


# Video Operations
def add_video(title: str, description: str, file_id: str, file_path: str = None, 
              transcript: str = None, concepts: list = None, difficulty_level: int = 1) -> Video:
    """Add a new video to the database"""
    with get_db() as db:
        video = Video(
            title=title,
            description=description,
            file_id=file_id,
            file_path=file_path,
            transcript=transcript,
            concepts=json.dumps(concepts) if concepts else None,
            difficulty_level=difficulty_level
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        return video


def get_next_video_for_user(user_id: int) -> Optional[Video]:
    """Get the next unwatched video for a user"""
    with get_db() as db:
        # Get videos the user hasn't watched
        watched_video_ids = db.query(VideoProgress.video_id).filter(
            VideoProgress.user_id == user_id,
            VideoProgress.completed == True
        ).all()
        watched_ids = [v[0] for v in watched_video_ids]
        
        # Get next video
        video = db.query(Video).filter(
            Video.is_active == True,
            Video.id.notin_(watched_ids)
        ).order_by(Video.order_index, Video.created_at).first()
        
        return video


def get_video_by_id(video_id: int) -> Optional[Video]:
    """Get a single video by ID"""
    with get_db() as db:
        return db.query(Video).filter(Video.id == video_id).first()


def mark_video_watched(user_id: int, video_id: int, completed: bool = True, watch_time: int = 0):
    """Mark a video as watched by a user"""
    with get_db() as db:
        progress = VideoProgress(
            user_id=user_id,
            video_id=video_id,
            completed=completed,
            watch_time=watch_time
        )
        db.add(progress)
        db.commit()


# Per-platform Media Operations (upload once, deliver many)
def get_media_ref(video_id: int, platform: str) -> Optional[str]:
    """
    Get the reusable media reference for a video on a platform.

    Falls back to the legacy videos.file_id column for Telegram so videos
    uploaded before multi-platform support still deliver.
    """
    with get_db() as db:
        record = db.query(VideoMedia).filter(
            VideoMedia.video_id == video_id,
            VideoMedia.platform == platform,
            VideoMedia.is_active == True
        ).first()

        if record:
            if record.expires_at and record.expires_at <= datetime.utcnow():
                return None
            return record.media_ref

        if platform == "telegram":
            video = db.query(Video).filter(Video.id == video_id).first()
            return video.file_id if video else None

        return None


def set_media_ref(video_id: int, platform: str, media_ref: str,
                  file_size_bytes: int = None, ttl_days: int = None) -> VideoMedia:
    """Store (or refresh) a platform media reference for a video"""
    with get_db() as db:
        record = db.query(VideoMedia).filter(
            VideoMedia.video_id == video_id,
            VideoMedia.platform == platform
        ).first()

        expires_at = datetime.utcnow() + timedelta(days=ttl_days) if ttl_days else None

        if record:
            record.media_ref = media_ref
            record.file_size_bytes = file_size_bytes
            record.uploaded_at = datetime.utcnow()
            record.expires_at = expires_at
            record.is_active = True
        else:
            record = VideoMedia(
                video_id=video_id,
                platform=platform,
                media_ref=media_ref,
                file_size_bytes=file_size_bytes,
                expires_at=expires_at
            )
            db.add(record)

        # Keep the legacy column in sync so older code paths keep working
        if platform == "telegram":
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.file_id = media_ref

        db.commit()
        db.refresh(record)
        return record


def list_media_refs(video_id: int) -> List[VideoMedia]:
    """All platform media references for a video"""
    with get_db() as db:
        return db.query(VideoMedia).filter(VideoMedia.video_id == video_id).all()


# Question Operations
def add_question(video_id: int, question_text: str, question_type: str = "open",
                correct_answer: str = None, concepts_tested: list = None, difficulty: int = 1) -> Question:
    """Add a question for a video"""
    with get_db() as db:
        question = Question(
            video_id=video_id,
            question_text=question_text,
            question_type=question_type,
            correct_answer=correct_answer,
            concepts_tested=json.dumps(concepts_tested) if concepts_tested else None,
            difficulty=difficulty
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question


def get_questions_for_video(video_id: int) -> List[Question]:
    """Get all questions for a video"""
    with get_db() as db:
        return db.query(Question).filter(
            Question.video_id == video_id,
            Question.is_active == True
        ).all()


def save_quiz_attempt(user_id: int, question_id: int, user_answer: str,
                     rating: float = None, feedback: str = None, 
                     is_correct: bool = None, time_taken: int = None):
    """Save a user's quiz attempt"""
    with get_db() as db:
        attempt = QuizAttempt(
            user_id=user_id,
            question_id=question_id,
            user_answer=user_answer,
            rating=rating,
            feedback=feedback,
            is_correct=is_correct,
            time_taken=time_taken
        )
        db.add(attempt)
        db.commit()


# Document Operations
def add_document(title: str, doc_type: str, file_path: str, content: str = None, metadata: dict = None) -> Document:
    """Add a document to the database"""
    with get_db() as db:
        document = Document(
            title=title,
            doc_type=doc_type,
            file_path=file_path,
            content=content,
            doc_metadata=json.dumps(metadata) if metadata else None
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document


def get_active_documents() -> List[Document]:
    """Get all active documents"""
    with get_db() as db:
        return db.query(Document).filter(Document.is_active == True).all()


# Session Operations
def create_user_session(user_id: int, session_type: str, context: dict = None) -> UserSession:
    """Create a new user session"""
    with get_db() as db:
        session = UserSession(
            user_id=user_id,
            session_type=session_type,
            context=json.dumps(context) if context else None
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session


def get_active_session(user_id: int, session_type: str = None) -> Optional[UserSession]:
    """Get active session for user"""
    with get_db() as db:
        query = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        )
        if session_type:
            query = query.filter(UserSession.session_type == session_type)
        return query.order_by(UserSession.started_at.desc()).first()


def end_session(session_id: int):
    """End a user session"""
    with get_db() as db:
        session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if session:
            session.is_active = False
            session.ended_at = datetime.utcnow()
            db.commit()


# Analytics Operations
def get_user_progress(user_id: int) -> dict:
    """Get user progress statistics"""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        total_videos = db.query(Video).filter(Video.is_active == True).count()
        watched_videos = db.query(VideoProgress).filter(
            VideoProgress.user_id == user_id,
            VideoProgress.completed == True
        ).count()
        
        total_questions = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id
        ).count()
        
        avg_rating = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.rating != None
        ).with_entities(QuizAttempt.rating).all()
        
        avg_score = sum([r[0] for r in avg_rating]) / len(avg_rating) if avg_rating else 0
        
        return {
            "total_videos": total_videos,
            "watched_videos": watched_videos,
            "completion_rate": (watched_videos / total_videos * 100) if total_videos > 0 else 0,
            "total_questions_answered": total_questions,
            "average_score": round(avg_score, 2)
        }
