"""Unit tests for SQLAlchemy models and DB operations."""
import pytest
from database.models import User, Video, VideoProgress, Question, QuizAttempt, Document, UserSession


class TestUserModel:
    def test_create_user(self, db_session):
        user = User(telegram_id="123456789", username="testuser", first_name="Test", role="learner")
        db_session.add(user)
        db_session.flush()

        assert user.id is not None
        assert user.role == "learner"
        assert user.is_active is True

    def test_user_telegram_id_unique(self, db_session):
        from sqlalchemy.exc import IntegrityError
        db_session.add(User(telegram_id="duplicate_id"))
        db_session.flush()
        db_session.add(User(telegram_id="duplicate_id"))
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()


class TestVideoModel:
    def test_create_video(self, db_session):
        video = Video(
            title="Intro to Python",
            file_id="tg_file_abc123",
            category="technical",
            order_index=1,
        )
        db_session.add(video)
        db_session.flush()

        assert video.id is not None
        assert video.is_active is True
        assert video.category == "technical"

    def test_video_question_relationship(self, db_session):
        video = Video(title="ML Basics", file_id="tg_file_xyz")
        db_session.add(video)
        db_session.flush()

        question = Question(video_id=video.id, question_text="What is supervised learning?")
        db_session.add(question)
        db_session.flush()

        assert len(video.questions) == 1
        assert video.questions[0].question_text == "What is supervised learning?"


class TestDocumentModel:
    def test_create_document(self, db_session):
        doc = Document(
            title="Employee Handbook",
            doc_type="manual",
            file_path="/data/documents/handbook.pdf",
            chunk_count=42,
        )
        db_session.add(doc)
        db_session.flush()

        assert doc.id is not None
        assert doc.is_active is True


class TestUserSessionModel:
    def test_create_session(self, db_session):
        user = User(telegram_id="sess_test_user")
        db_session.add(user)
        db_session.flush()

        session_obj = UserSession(user_id=user.id, session_type="quiz", is_active=True)
        db_session.add(session_obj)
        db_session.flush()

        assert session_obj.id is not None
        assert session_obj.session_type == "quiz"
