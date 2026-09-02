"""
Telegram implementation of MessagingClient (python-telegram-bot).
"""
import os
from typing import Optional

from loguru import logger
from telegram import Bot
from telegram.error import (
    BadRequest,
    Forbidden,
    InvalidToken,
    NetworkError,
    RetryAfter,
    TelegramError,
    TimedOut,
)

from messaging.base import (
    Choice,
    MessagingClient,
    OutboundResult,
    PermanentMessagingError,
    Platform,
    TransientMessagingError,
)


class TelegramClient(MessagingClient):
    """Wraps a python-telegram-bot Bot behind the MessagingClient interface."""

    platform = Platform.TELEGRAM
    max_text_chars = 4096
    max_caption_chars = 1024
    max_video_bytes = 50 * 1024 * 1024  # Bot API upload limit

    def __init__(self, bot: Bot):
        self.bot = bot

    # -- outbound ---------------------------------------------------------

    async def _send_markdown(self, **kwargs):
        """
        Send with Markdown parsing, falling back to plain text.

        Messages are authored with WhatsApp's syntax (see messaging.formatting)
        and Telegram's legacy Markdown reads the same *bold* / _italic_ markers,
        so one string serves both channels.

        Where they differ is failure: WhatsApp shows an unbalanced marker
        literally, while Telegram rejects the whole send with a 400. Our own
        copy is balanced and model output is sanitized, but a learner's own
        words get quoted back to them - so an unparseable message is delivered
        plain rather than dropped.
        """
        from telegram.constants import ParseMode

        try:
            return await self.bot.send_message(parse_mode=ParseMode.MARKDOWN, **kwargs)
        except BadRequest as exc:
            detail = str(exc).lower()
            if "parse" not in detail and "entit" not in detail:
                raise
            logger.debug(f"Markdown parse failed, resending as plain text: {exc}")
            return await self.bot.send_message(**kwargs)

    async def send_message(self, to: str, text: str) -> OutboundResult:
        message_id = None
        try:
            for part in self.split_message(text):
                message = await self._send_markdown(chat_id=to, text=part)
                message_id = str(message.message_id)
        except Exception as exc:
            raise _translate(exc) from exc

        return OutboundResult(success=True, platform=self.platform, message_id=message_id)

    async def send_choices(
        self,
        to: str,
        text: str,
        choices,
        *,
        header: Optional[str] = None,
        footer: Optional[str] = None,
        list_label: str = "Menu",
    ) -> OutboundResult:
        """
        Send a menu as an inline keyboard.

        Telegram has native slash commands, but the same menus still need to
        work here or the two channels drift - a learner tapping "Take a quiz"
        must reach the same dispatcher path on both. `callback_data` carries
        the choice id, which main.py hands straight to the dispatcher.
        """
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        choices = list(choices or [])
        if not choices:
            return await self.send_message(to, text)

        body = "\n\n".join(part for part in (header, text, footer) if part)
        keyboard = [
            # One per row: these are sentences, not chips, and wrap badly side by side.
            [InlineKeyboardButton(str(c.title), callback_data=str(c.id)[:64])]
            for c in choices
        ]

        try:
            message = await self._send_markdown(
                chat_id=to,
                text=body or "Choose an option",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as exc:
            raise _translate(exc) from exc

        return OutboundResult(
            success=True, platform=self.platform, message_id=str(message.message_id)
        )

    async def send_video(self, to: str, media_ref: str, caption: str = "") -> OutboundResult:
        if not media_ref:
            raise PermanentMessagingError(
                "No Telegram file_id available for this video",
                platform=self.platform,
                suggestion="Upload the video once with VideoUploadAgent to obtain a file_id.",
            )

        try:
            message = await self.bot.send_video(
                chat_id=to,
                video=media_ref,
                caption=self.truncate_caption(caption),
                supports_streaming=True,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=20,
                pool_timeout=20,
            )
        except Exception as exc:
            raise _translate(exc) from exc

        return OutboundResult(
            success=True,
            platform=self.platform,
            message_id=str(message.message_id),
            media_ref=message.video.file_id if message.video else media_ref,
        )

    async def upload_video(self, file_path: str, *, staging_chat_id: Optional[str] = None) -> OutboundResult:
        """
        Telegram has no standalone upload endpoint - a video becomes a reusable
        file_id only once it has been sent somewhere. The file is buffered in
        memory first so filesystem I/O never overlaps with the HTTP upload
        (the root cause of the original Windows/OneDrive upload timeouts).
        """
        if not staging_chat_id:
            raise PermanentMessagingError(
                "Telegram uploads need a staging chat",
                platform=self.platform,
                suggestion="Set TELEGRAM_UPLOAD_STAGING_CHAT_ID (or ADMIN_CHAT_ID) to a chat the bot can post in.",
            )

        if not os.path.exists(file_path):
            raise PermanentMessagingError(
                f"Video file not found: {file_path}",
                platform=self.platform,
                suggestion="Check the file path stored on the video record.",
            )

        size = os.path.getsize(file_path)
        if size > self.max_video_bytes:
            raise PermanentMessagingError(
                f"Video is {size / 1024 / 1024:.1f} MB; Telegram bots can upload at most "
                f"{self.max_video_bytes / 1024 / 1024:.0f} MB",
                platform=self.platform,
                suggestion="Compress the video or host it and send by URL.",
            )

        with open(file_path, "rb") as handle:
            buffer = handle.read()

        try:
            message = await self.bot.send_video(
                chat_id=staging_chat_id,
                video=buffer,
                caption=f"Uploaded: {os.path.basename(file_path)}",
                supports_streaming=True,
                read_timeout=300,
                write_timeout=300,
                connect_timeout=60,
                pool_timeout=60,
            )
        except Exception as exc:
            raise _translate(exc) from exc

        file_id = message.video.file_id if message.video else None
        if not file_id:
            raise PermanentMessagingError(
                "Telegram accepted the upload but returned no file_id",
                platform=self.platform,
            )

        logger.info(f"Telegram upload cached file_id for {os.path.basename(file_path)}")
        return OutboundResult(
            success=True,
            platform=self.platform,
            message_id=str(message.message_id),
            media_ref=file_id,
        )


def _translate(exc: Exception) -> Exception:
    """Map python-telegram-bot exceptions onto the shared error taxonomy."""
    if isinstance(exc, RetryAfter):
        return TransientMessagingError(
            f"Rate limited by Telegram, retry in {exc.retry_after}s",
            platform=Platform.TELEGRAM,
            suggestion="Slow down the send rate.",
        )

    if isinstance(exc, Forbidden):
        return PermanentMessagingError(
            f"Telegram refused delivery: {exc}",
            platform=Platform.TELEGRAM,
            suggestion="The user has blocked the bot or never pressed /start.",
        )

    if isinstance(exc, InvalidToken):
        return PermanentMessagingError(
            "Invalid TELEGRAM_BOT_TOKEN",
            platform=Platform.TELEGRAM,
            suggestion="Check TELEGRAM_BOT_TOKEN in your .env file.",
        )

    if isinstance(exc, BadRequest):
        text = str(exc).lower()
        if "file" in text:
            suggestion = "The file_id is invalid or expired - re-upload the video."
        elif "chat not found" in text:
            suggestion = "Chat not found - the user may have deleted their account."
        else:
            suggestion = "Check the request parameters."
        return PermanentMessagingError(
            f"Telegram rejected the request: {exc}",
            platform=Platform.TELEGRAM,
            suggestion=suggestion,
        )

    if isinstance(exc, (TimedOut, NetworkError)):
        return TransientMessagingError(
            f"Telegram network problem: {exc}",
            platform=Platform.TELEGRAM,
            suggestion="Check connectivity and Telegram API status.",
        )

    if isinstance(exc, TelegramError):
        return TransientMessagingError(
            f"Telegram error: {exc}",
            platform=Platform.TELEGRAM,
        )

    return exc
