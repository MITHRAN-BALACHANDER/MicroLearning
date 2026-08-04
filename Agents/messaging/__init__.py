"""
Platform-agnostic messaging layer.

The agents talk to `MessagingRouter` instead of a concrete SDK, so the same
learning logic runs over Telegram, WhatsApp, or both, selected by the
MESSAGING_PLATFORM environment flag.
"""
from messaging.base import (
    MessagingClient,
    MessagingError,
    OutboundResult,
    PermanentMessagingError,
    Platform,
    TransientMessagingError,
    UserRef,
    split_text,
)
from messaging.router import MessagingRouter

__all__ = [
    "MessagingClient",
    "MessagingError",
    "MessagingRouter",
    "OutboundResult",
    "PermanentMessagingError",
    "Platform",
    "TransientMessagingError",
    "UserRef",
    "split_text",
]
