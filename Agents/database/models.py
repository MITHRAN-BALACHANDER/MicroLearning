"""
Database models for the MicroLearning Bot
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model for tracking learners across messaging platforms"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Platform-qualified unique key. Telegram users keep their bare chat id so
    # existing rows are untouched; other platforms are namespaced ("whatsapp:15551234567").
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    # Which channel this learner uses, and the raw id needed to message them.
    platform = Column(String, default='telegram', index=True, nullable=False)
    platform_user_id = Column(String, nullable=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    role = Column(String, default='learner')  # learner, instructor, admin
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    # Last inbound message time; WhatsApp only allows free-form replies within
    # 24h of this, after which an approved template is required.
    last_inbound_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    videos_watched = relationship("VideoProgress", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")

    @property
    def user_key(self) -> str:
        """The platform-qualified key (alias for the legacy column name)."""
        return self.telegram_id


class Video(Base):
    """Video model for storing learning content"""
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    file_id = Column(String, nullable=False)  # Telegram file_id
    file_path = Column(String, nullable=True)  # Local path
    duration = Column(Integer, nullable=True)  # Duration in seconds
    transcript = Column(Text, nullable=True)
    concepts = Column(Text, nullable=True)  # JSON string of key concepts
    category = Column(String, default='general')  # general, technical, business, onboarding
    difficulty_level = Column(Integer, default=1)  # 1-5
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    progress_records = relationship("VideoProgress", back_populates="video")
    questions = relationship("Question", back_populates="video")
    media_refs = relationship("VideoMedia", back_populates="video", cascade="all, delete-orphan")


class VideoMedia(Base):
    """
    Per-platform media reference for a video (upload once, deliver many).

    Each platform hands back its own opaque handle after the first upload:
      - Telegram: file_id (does not expire)
      - WhatsApp: media id (expires ~30 days) or a public URL
    """
    __tablename__ = "video_media"
    __table_args__ = (UniqueConstraint("video_id", "platform", name="uq_video_media_platform"),)

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    platform = Column(String, nullable=False, index=True)  # telegram, whatsapp
    media_ref = Column(String, nullable=False)  # file_id / media id / public URL
    file_size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # WhatsApp media ids expire
    is_active = Column(Boolean, default=True)

    video = relationship("Video", back_populates="media_refs")


class VideoProgress(Base):
    """Track user progress on videos"""
    __tablename__ = "video_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    watched_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)
    watch_time = Column(Integer, default=0)  # Seconds watched
    
    # Relationships
    user = relationship("User", back_populates="videos_watched")
    video = relationship("Video", back_populates="progress_records")


class Question(Base):
    """Questions generated from video content"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, default="open")  # open, multiple_choice
    correct_answer = Column(Text, nullable=True)
    concepts_tested = Column(Text, nullable=True)  # JSON string
    difficulty = Column(Integer, default=1)  # 1-5
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    video = relationship("Video", back_populates="questions")
    attempts = relationship("QuizAttempt", back_populates="question")


class QuizAttempt(Base):
    """User attempts at answering questions"""
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)  # 0-10
    feedback = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    attempted_at = Column(DateTime, default=datetime.utcnow)
    time_taken = Column(Integer, nullable=True)  # Seconds
    
    # Relationships
    user = relationship("User", back_populates="quiz_attempts")
    question = relationship("Question", back_populates="attempts")


class Document(Base):
    """Company documents for RAG"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)  # manual, sop, policy
    file_path = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    doc_metadata = Column(Text, nullable=True)  # JSON string - renamed from 'metadata' to avoid conflict
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    chunk_count = Column(Integer, default=0)


class UserSession(Base):
    """Track user sessions and conversation context"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_type = Column(String, nullable=False)  # video, quiz, rag
    context = Column(Text, nullable=True)  # JSON string
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
