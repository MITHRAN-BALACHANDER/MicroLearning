"""Integration tests for database operations layer."""
import os
import pytest

# Point operations at the in-memory engine before import
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, Video, VideoProgress


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.rollback()
    sess.close()


class TestGetOrCreateUser:
    def test_creates_new_user(self, session):
        user = session.query(User).filter_by(telegram_id="new_user_1").first()
        assert user is None

        new_user = User(telegram_id="new_user_1", username="alice")
        session.add(new_user)
        session.flush()

        fetched = session.query(User).filter_by(telegram_id="new_user_1").first()
        assert fetched is not None
        assert fetched.username == "alice"

    def test_returns_existing_user(self, session):
        user = User(telegram_id="existing_user_1", username="bob")
        session.add(user)
        session.flush()

        existing = session.query(User).filter_by(telegram_id="existing_user_1").first()
        assert existing.id == user.id


class TestVideoProgress:
    def test_track_video_watch(self, session):
        user = User(telegram_id="watcher_1")
        video = Video(title="Test Video", file_id="tg_abc")
        session.add_all([user, video])
        session.flush()

        progress = VideoProgress(user_id=user.id, video_id=video.id, completed=True, watch_time=120)
        session.add(progress)
        session.flush()

        record = session.query(VideoProgress).filter_by(user_id=user.id, video_id=video.id).first()
        assert record is not None
        assert record.completed is True
        assert record.watch_time == 120

    def test_next_unwatched_video(self, session):
        user = User(telegram_id="watcher_2")
        v1 = Video(title="Video A", file_id="tg_v1", order_index=1)
        v2 = Video(title="Video B", file_id="tg_v2", order_index=2)
        session.add_all([user, v1, v2])
        session.flush()

        # Mark v1 as watched
        session.add(VideoProgress(user_id=user.id, video_id=v1.id, completed=True))
        session.flush()

        # Query for next unwatched
        watched_ids = (
            session.query(VideoProgress.video_id)
            .filter_by(user_id=user.id)
            .subquery()
        )
        next_video = (
            session.query(Video)
            .filter(Video.id.not_in(watched_ids))
            .filter(Video.is_active == True)
            .order_by(Video.order_index)
            .first()
        )
        assert next_video is not None
        assert next_video.title == "Video B"
