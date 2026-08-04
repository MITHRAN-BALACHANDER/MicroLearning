"""
Tests for the multi-platform data model: user keys, per-platform media
references, and the additive migration that upgrades an existing database.
"""
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from database.migrations import ensure_schema
from database.models import Base, User, Video, VideoMedia
from messaging.base import Platform, UserRef


class TestUserModel:
    def test_platform_defaults_to_telegram(self, db_session):
        user = User(telegram_id="123", platform="telegram")
        db_session.add(user)
        db_session.flush()
        assert user.platform == "telegram"

    def test_whatsapp_user_stores_namespaced_key_and_raw_id(self, db_session):
        ref = UserRef(Platform.WHATSAPP, "15551234567")
        user = User(
            telegram_id=ref.key,
            platform=ref.platform.value,
            platform_user_id=ref.platform_user_id,
        )
        db_session.add(user)
        db_session.flush()

        assert user.telegram_id == "whatsapp:15551234567"
        assert user.platform_user_id == "15551234567"
        assert user.user_key == "whatsapp:15551234567"

    def test_same_number_on_both_platforms_can_coexist(self, db_session):
        """The namespaced key is what makes this possible."""
        db_session.add(User(telegram_id=UserRef(Platform.TELEGRAM, "15551234567").key,
                            platform="telegram", platform_user_id="15551234567"))
        db_session.add(User(telegram_id=UserRef(Platform.WHATSAPP, "15551234567").key,
                            platform="whatsapp", platform_user_id="15551234567"))
        db_session.flush()

        assert db_session.query(User).count() == 2


class TestVideoMedia:
    def _video(self, db_session, title="Intro"):
        video = Video(title=title, file_id="legacy_tg_file_id")
        db_session.add(video)
        db_session.flush()
        return video

    def test_one_video_can_have_a_ref_per_platform(self, db_session):
        video = self._video(db_session)
        db_session.add(VideoMedia(video_id=video.id, platform="telegram", media_ref="tg_abc"))
        db_session.add(VideoMedia(video_id=video.id, platform="whatsapp", media_ref="wa_123"))
        db_session.flush()

        refs = {m.platform: m.media_ref for m in video.media_refs}
        assert refs == {"telegram": "tg_abc", "whatsapp": "wa_123"}

    def test_platform_is_unique_per_video(self, db_session):
        from sqlalchemy.exc import IntegrityError

        video = self._video(db_session, title="Unique test")
        db_session.add(VideoMedia(video_id=video.id, platform="whatsapp", media_ref="one"))
        db_session.flush()
        db_session.add(VideoMedia(video_id=video.id, platform="whatsapp", media_ref="two"))

        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()


class TestAdditiveMigration:
    """
    An existing microlearning.db predates the platform columns. ensure_schema
    must add them in place without touching the rows already there.
    """

    def _legacy_engine(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    telegram_id VARCHAR NOT NULL UNIQUE,
                    username VARCHAR,
                    first_name VARCHAR,
                    last_name VARCHAR,
                    role VARCHAR,
                    created_at TIMESTAMP,
                    last_active TIMESTAMP,
                    is_active BOOLEAN
                )
            """))
            conn.execute(text(
                "INSERT INTO users (telegram_id, first_name) VALUES ('6437411483', 'Mithran')"
            ))
        return engine

    def test_adds_the_new_columns(self):
        engine = self._legacy_engine()
        applied = ensure_schema(engine)

        columns = {c["name"] for c in inspect(engine).get_columns("users")}
        assert {"platform", "platform_user_id", "last_inbound_at"} <= columns
        assert "users.platform" in applied

    def test_backfills_existing_rows_as_telegram(self):
        engine = self._legacy_engine()
        ensure_schema(engine)

        with engine.connect() as conn:
            row = conn.execute(text(
                "SELECT telegram_id, platform, platform_user_id, first_name FROM users"
            )).fetchone()

        assert row[0] == "6437411483"
        assert row[1] == "telegram"
        assert row[2] == "6437411483"   # raw id backfilled for sending
        assert row[3] == "Mithran"      # existing data untouched

    def test_is_idempotent(self):
        engine = self._legacy_engine()
        ensure_schema(engine)
        assert ensure_schema(engine) == []

    def test_no_op_on_a_fresh_database(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        assert ensure_schema(engine) == []


class TestMediaRefResolution:
    """get_media_ref falls back to the legacy videos.file_id for Telegram."""

    @pytest.fixture
    def ops(self, monkeypatch):
        import database.operations as operations

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        monkeypatch.setattr(operations, "engine", engine)
        monkeypatch.setattr(operations, "SessionLocal", Session)
        return operations

    def test_legacy_file_id_is_used_for_telegram(self, ops):
        with ops.get_db() as db:
            video = Video(title="Legacy", file_id="BAACAgIAAxkBAAI_legacy")
            db.add(video)
            db.commit()
            video_id = video.id

        assert ops.get_media_ref(video_id, "telegram") == "BAACAgIAAxkBAAI_legacy"

    def test_whatsapp_has_no_legacy_fallback(self, ops):
        with ops.get_db() as db:
            video = Video(title="Legacy", file_id="BAACAgIAAxkBAAI_legacy")
            db.add(video)
            db.commit()
            video_id = video.id

        assert ops.get_media_ref(video_id, "whatsapp") is None

    def test_set_media_ref_round_trips(self, ops):
        with ops.get_db() as db:
            video = Video(title="New", file_id="x")
            db.add(video)
            db.commit()
            video_id = video.id

        ops.set_media_ref(video_id, "whatsapp", "wa-media-999", file_size_bytes=1024, ttl_days=28)

        assert ops.get_media_ref(video_id, "whatsapp") == "wa-media-999"

    def test_expired_whatsapp_ref_is_ignored(self, ops):
        from datetime import datetime, timedelta

        with ops.get_db() as db:
            video = Video(title="Expiring", file_id="x")
            db.add(video)
            db.commit()
            video_id = video.id

            db.add(VideoMedia(
                video_id=video_id, platform="whatsapp", media_ref="stale",
                expires_at=datetime.utcnow() - timedelta(days=1),
            ))
            db.commit()

        assert ops.get_media_ref(video_id, "whatsapp") is None

    def test_setting_a_telegram_ref_syncs_the_legacy_column(self, ops):
        with ops.get_db() as db:
            video = Video(title="Sync", file_id="old_id")
            db.add(video)
            db.commit()
            video_id = video.id

        ops.set_media_ref(video_id, "telegram", "new_file_id")

        with ops.get_db() as db:
            assert db.query(Video).filter(Video.id == video_id).first().file_id == "new_file_id"

    def test_user_created_from_ref_is_platform_aware(self, ops):
        ref = UserRef(Platform.WHATSAPP, "15551234567")
        user = ops.get_or_create_user_from_ref(ref, first_name="Alice")

        assert user.telegram_id == "whatsapp:15551234567"
        assert user.platform == "whatsapp"
        assert user.platform_user_id == "15551234567"
        assert user.last_inbound_at is not None

        assert ops.get_user_by_ref(ref).id == user.id

    def test_get_or_create_is_idempotent(self, ops):
        ref = UserRef(Platform.WHATSAPP, "15551234567")
        first = ops.get_or_create_user_from_ref(ref, first_name="Alice")
        second = ops.get_or_create_user_from_ref(ref, first_name="Alice")

        assert first.id == second.id
