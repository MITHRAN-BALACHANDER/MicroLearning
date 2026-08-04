"""
MessagingRouter - dispatches outbound messages to the right platform client.

Agents depend on this instead of a platform SDK, so the same learning logic
serves Telegram and WhatsApp users simultaneously.
"""
import asyncio
from typing import Dict, Iterable, List, Optional

from loguru import logger

from messaging.base import (
    MessagingClient,
    MessagingError,
    OutboundResult,
    PermanentMessagingError,
    Platform,
    TransientMessagingError,
    UserRef,
)


class MessagingRouter:
    """Holds one client per enabled platform and routes by UserRef.platform."""

    def __init__(self, clients: Dict[Platform, MessagingClient]):
        if not clients:
            raise ValueError("MessagingRouter needs at least one platform client")
        self.clients: Dict[Platform, MessagingClient] = dict(clients)
        logger.info(
            "MessagingRouter enabled for: "
            + ", ".join(p.value for p in self.clients)
        )

    # -- lookup -----------------------------------------------------------

    @property
    def platforms(self) -> List[Platform]:
        return list(self.clients)

    def is_enabled(self, platform) -> bool:
        return Platform.parse(platform) in self.clients

    def client_for(self, target) -> MessagingClient:
        """Resolve the client for a UserRef or a bare platform."""
        platform = target.platform if isinstance(target, UserRef) else Platform.parse(target)
        client = self.clients.get(platform)
        if client is None:
            enabled = ", ".join(p.value for p in self.clients) or "none"
            raise PermanentMessagingError(
                f"Platform '{platform.value}' is not enabled (enabled: {enabled})",
                platform=platform,
                suggestion="Add it to MESSAGING_PLATFORM in your .env file and restart.",
            )
        return client

    def limits_for(self, target) -> MessagingClient:
        """Alias kept readable at call sites that only want caption/text limits."""
        return self.client_for(target)

    # -- outbound ---------------------------------------------------------

    async def send_message(self, ref: UserRef, text: str, *, max_retries: int = 3) -> OutboundResult:
        """
        Send text to a learner, retrying transient failures with backoff.

        Never raises: agents get a result object so a failed send degrades the
        turn instead of crashing the handler.
        """
        client = self.client_for(ref)
        last_error: Optional[MessagingError] = None

        for attempt in range(1, max_retries + 1):
            try:
                result = await client.send_message(ref.platform_user_id, text)
                result.attempts = attempt
                return result
            except TransientMessagingError as exc:
                last_error = exc
                logger.warning(
                    f"Transient send failure to {ref} (attempt {attempt}/{max_retries}): {exc}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 2)
            except PermanentMessagingError as exc:
                logger.error(f"Permanent send failure to {ref}: {exc} | {exc.suggestion}")
                return OutboundResult(
                    success=False,
                    platform=ref.platform,
                    error=str(exc),
                    suggestion=exc.suggestion,
                    attempts=attempt,
                )
            except Exception as exc:  # noqa: BLE001 - never let a send kill the turn
                logger.exception(f"Unexpected send failure to {ref}")
                return OutboundResult(
                    success=False,
                    platform=ref.platform,
                    error=str(exc),
                    attempts=attempt,
                )

        return OutboundResult(
            success=False,
            platform=ref.platform,
            error=str(last_error) if last_error else "Send failed",
            suggestion=last_error.suggestion if last_error else "",
            attempts=max_retries,
        )

    async def send_video(self, ref: UserRef, media_ref: str, caption: str = "") -> OutboundResult:
        """Single-attempt video send. VideoDeliveryAgent adds retry/backoff."""
        client = self.client_for(ref)
        return await client.send_video(ref.platform_user_id, media_ref, caption)

    async def upload_video(self, platform, file_path: str, *, staging_chat_id: Optional[str] = None) -> OutboundResult:
        client = self.client_for(platform)
        return await client.upload_video(file_path, staging_chat_id=staging_chat_id)

    async def mark_read(self, ref: UserRef, message_id: Optional[str]) -> None:
        if not message_id:
            return
        try:
            await self.client_for(ref).mark_read(message_id)
        except Exception as exc:  # noqa: BLE001 - cosmetic only
            logger.debug(f"mark_read failed for {ref}: {exc}")

    async def broadcast(self, refs: Iterable[UserRef], text: str) -> Dict[str, OutboundResult]:
        """Send the same text to many learners across platforms."""
        refs = list(refs)
        results = await asyncio.gather(
            *(self.send_message(ref, text) for ref in refs),
            return_exceptions=True,
        )
        out: Dict[str, OutboundResult] = {}
        for ref, result in zip(refs, results):
            if isinstance(result, Exception):
                out[ref.key] = OutboundResult(
                    success=False, platform=ref.platform, error=str(result)
                )
            else:
                out[ref.key] = result
        return out

    async def close(self) -> None:
        for client in self.clients.values():
            try:
                await client.close()
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"Error closing {client.platform.value} client: {exc}")

    def get_state(self) -> Dict[str, object]:
        return {
            "platforms": [p.value for p in self.clients],
            "limits": {
                p.value: {
                    "max_text_chars": c.max_text_chars,
                    "max_caption_chars": c.max_caption_chars,
                    "max_video_mb": round(c.max_video_bytes / 1024 / 1024),
                }
                for p, c in self.clients.items()
            },
        }
