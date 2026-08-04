"""Shared pytest fixtures."""
import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))

# Use in-memory SQLite so tests never need a real DB
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test:token")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("AGNO_API_KEY", "test-key")
os.environ.setdefault("VIDEOS_DIR", str(Path(__file__).parent / "_tmp_videos"))

# WhatsApp settings used by the webhook and client tests
os.environ.setdefault("WHATSAPP_ACCESS_TOKEN", "test-wa-token")
os.environ.setdefault("WHATSAPP_PHONE_NUMBER_ID", "111222333444555")
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "test-verify-token")
os.environ.setdefault("WHATSAPP_APP_SECRET", "test-app-secret")

from database.models import Base  # noqa: E402


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


class FakeClient:
    """In-memory MessagingClient double that records what was sent."""

    def __init__(self, platform, max_text_chars=4096, max_caption_chars=1024):
        from messaging.base import Platform

        self.platform = Platform.parse(platform)
        self.max_text_chars = max_text_chars
        self.max_caption_chars = max_caption_chars
        self.max_video_bytes = 16 * 1024 * 1024
        self.messages = []
        self.videos = []
        self.read_receipts = []
        self.fail_with = None

    def truncate_caption(self, caption):
        if caption and len(caption) > self.max_caption_chars:
            return caption[: self.max_caption_chars - 3] + "..."
        return caption

    def split_message(self, text):
        from messaging.base import split_text

        return split_text(text, self.max_text_chars)

    async def send_message(self, to, text):
        from messaging.base import OutboundResult

        if self.fail_with:
            raise self.fail_with
        self.messages.append((to, text))
        return OutboundResult(success=True, platform=self.platform, message_id=f"m{len(self.messages)}")

    async def send_video(self, to, media_ref, caption=""):
        from messaging.base import OutboundResult

        if self.fail_with:
            raise self.fail_with
        self.videos.append((to, media_ref, caption))
        return OutboundResult(
            success=True, platform=self.platform,
            message_id=f"v{len(self.videos)}", media_ref=media_ref
        )

    async def upload_video(self, file_path, *, staging_chat_id=None):
        from messaging.base import OutboundResult

        return OutboundResult(success=True, platform=self.platform, media_ref="uploaded-ref")

    async def mark_read(self, message_id):
        self.read_receipts.append(message_id)

    async def close(self):
        return None


@pytest.fixture
def fake_whatsapp_client():
    from messaging.base import Platform

    return FakeClient(Platform.WHATSAPP)


@pytest.fixture
def fake_telegram_client():
    from messaging.base import Platform

    return FakeClient(Platform.TELEGRAM)


@pytest.fixture
def router(fake_telegram_client, fake_whatsapp_client):
    from messaging.base import Platform
    from messaging.router import MessagingRouter

    return MessagingRouter({
        Platform.TELEGRAM: fake_telegram_client,
        Platform.WHATSAPP: fake_whatsapp_client,
    })
