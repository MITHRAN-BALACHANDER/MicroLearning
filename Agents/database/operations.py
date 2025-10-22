"""
Database operations and utility functions
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import List, Optional
from datetime import datetime, timedelta
import json

from database.models import Base, User, Video, VideoProgress, Question, QuizAttempt, Document, UserSession
from config.settings import DATABASE_URL


# Create engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# User Operations
def get_or_create_user(telegram_id: str, username: str = None, first_name: str = None, last_name: str = None) -> User:
    """Get or create a user"""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update last active
            user.last_active = datetime.utcnow()
            db.commit()
        return user


def get_user_by_telegram_id(telegram_id: str) -> Optional[User]:
    """Get user by telegram ID"""
    with get_db() as db:
        return db.query(User).filter(User.telegram_id == telegram_id).first()


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
