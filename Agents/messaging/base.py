"""
Core messaging types shared by every platform client.

Nothing in this module imports a platform SDK, so it is safe to import from
tests, the admin dashboard, and scripts without pulling in Telegram/WhatsApp
dependencies.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class Platform(str, Enum):
    """Messaging channels the platform can run on."""

    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"

    @classmethod
    def parse(cls, value) -> "Platform":
        """Coerce a string / enum into a Platform, with a helpful error."""
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value).strip().lower())
        except ValueError:
            valid = ", ".join(p.value for p in cls)
            raise ValueError(f"Unknown platform '{value}'. Valid platforms: {valid}")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class MessagingError(Exception):
    """Base class for send failures, normalised across platforms."""

    retryable = False

    def __init__(self, message: str, *, platform: Optional[Platform] = None,
                 code=None, suggestion: str = ""):
        super().__init__(message)
        self.message = message
        self.platform = platform
        self.code = code
        self.suggestion = suggestion


class TransientMessagingError(MessagingError):
    """Temporary failure (timeout, rate limit, 5xx) - retrying may succeed."""

    retryable = True


class PermanentMessagingError(MessagingError):
    """Permanent failure (bad credentials, blocked user, invalid media) - do not retry."""

    retryable = False


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UserRef:
    """
    Identifies a learner on a specific platform.

    `platform_user_id` is what the platform expects when sending:
      - Telegram: the numeric chat id
      - WhatsApp: the wa_id (E.164 digits, no leading '+')

    `key` is the value stored in `users.telegram_id`. Telegram ids are stored
    bare so existing rows keep working; other platforms are namespaced to avoid
    collisions across channels.
    """

    platform: Platform
    platform_user_id: str

    @property
    def key(self) -> str:
        if self.platform is Platform.TELEGRAM:
            return str(self.platform_user_id)
        return f"{self.platform.value}:{self.platform_user_id}"

    @classmethod
    def from_key(cls, key: str) -> "UserRef":
        """Rebuild a UserRef from a stored `users.telegram_id` value."""
        text = str(key)
        for platform in Platform:
            prefix = f"{platform.value}:"
            if text.startswith(prefix):
                return cls(platform, text[len(prefix):])
        return cls(Platform.TELEGRAM, text)

    @classmethod
    def telegram(cls, chat_id) -> "UserRef":
        return cls(Platform.TELEGRAM, str(chat_id))

    @classmethod
    def whatsapp(cls, wa_id) -> "UserRef":
        return cls(Platform.WHATSAPP, normalize_wa_id(wa_id))

    def __str__(self) -> str:
        return self.key


@dataclass
class OutboundResult:
    """Normalised result of a send/upload attempt."""

    success: bool
    platform: Platform
    message_id: Optional[str] = None
    media_ref: Optional[str] = None
    error: Optional[str] = None
    suggestion: str = ""
    attempts: int = 1


@dataclass
class InboundMessage:
    """Normalised inbound message from any platform."""

    ref: UserRef
    text: str
    message_id: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    message_type: str = "text"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def normalize_wa_id(value) -> str:
    """WhatsApp expects E.164 digits with no '+', spaces, or punctuation."""
    return "".join(ch for ch in str(value) if ch.isdigit())


def split_text(text: str, limit: int) -> List[str]:
    """
    Split text into chunks that fit the platform's per-message limit,
    preferring paragraph then line then word boundaries.
    """
    if limit <= 0:
        raise ValueError("limit must be positive")

    text = text or ""
    if len(text) <= limit:
        return [text]

    chunks: List[str] = []
    remaining = text

    while len(remaining) > limit:
        window = remaining[:limit]
        # Prefer to break on a paragraph, then a line, then a space.
        for separator in ("\n\n", "\n", " "):
            cut = window.rfind(separator)
            if cut > limit // 2:
                break
        else:
            cut = -1

        if cut <= 0:
            cut = limit

        chunks.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()

    if remaining:
        chunks.append(remaining)

    return chunks


# ---------------------------------------------------------------------------
# Client interface
# ---------------------------------------------------------------------------


class MessagingClient(ABC):
    """
    Interface every platform client implements.

    Subclasses declare their platform limits so callers can build captions and
    messages that the platform will actually accept.
    """

    platform: Platform = None
    max_text_chars: int = 4096
    max_caption_chars: int = 1024
    max_video_bytes: int = 50 * 1024 * 1024

    @abstractmethod
    async def send_message(self, to: str, text: str) -> OutboundResult:
        """Send a plain text message, splitting it if it exceeds the limit."""

    @abstractmethod
    async def send_video(self, to: str, media_ref: str, caption: str = "") -> OutboundResult:
        """Send a video by platform media reference (file_id / media id / URL)."""

    @abstractmethod
    async def upload_video(self, file_path: str, *, staging_chat_id: Optional[str] = None) -> OutboundResult:
        """Upload a video once and return a reusable media reference."""

    async def mark_read(self, message_id: str) -> None:
        """Optional read receipt. No-op unless the platform supports it."""
        return None

    async def close(self) -> None:
        """Release network resources. No-op by default."""
        return None

    # -- convenience ------------------------------------------------------

    def truncate_caption(self, caption: str) -> str:
        if caption and len(caption) > self.max_caption_chars:
            return caption[: self.max_caption_chars - 3] + "..."
        return caption

    def split_message(self, text: str) -> List[str]:
        return split_text(text, self.max_text_chars)
