"""
Builds the messaging clients selected by the MESSAGING_PLATFORM feature flag.

This is the single place that decides which channels the process runs on, and
the single place that validates each channel's credentials up front, so a
misconfigured deployment fails at startup with a clear message rather than at
the first user message.
"""
from typing import Dict, List, Optional, Tuple

from loguru import logger

from config import settings
from messaging.base import MessagingClient, Platform
from messaging.router import MessagingRouter


class PlatformConfigError(RuntimeError):
    """Raised when an enabled platform is missing required configuration."""


def enabled_platforms() -> List[Platform]:
    """Platforms selected by MESSAGING_PLATFORM, as enum members."""
    return [Platform.parse(name) for name in settings.ENABLED_PLATFORMS]


def validate_platform_config(platforms: Optional[List[Platform]] = None) -> Tuple[bool, List[str]]:
    """
    Check that every enabled platform has the settings it needs.

    Returns (ok, problems) instead of raising so pre-flight checks can print a
    full report rather than stopping at the first missing variable.
    """
    platforms = platforms or enabled_platforms()
    problems: List[str] = []

    if Platform.TELEGRAM in platforms and not settings.TELEGRAM_BOT_TOKEN:
        problems.append("TELEGRAM_BOT_TOKEN is required when telegram is enabled")

    if Platform.WHATSAPP in platforms:
        required = {
            "WHATSAPP_ACCESS_TOKEN": settings.WHATSAPP_ACCESS_TOKEN,
            "WHATSAPP_PHONE_NUMBER_ID": settings.WHATSAPP_PHONE_NUMBER_ID,
            "WHATSAPP_VERIFY_TOKEN": settings.WHATSAPP_VERIFY_TOKEN,
        }
        for name, value in required.items():
            if not value:
                problems.append(f"{name} is required when whatsapp is enabled")

        if not settings.WHATSAPP_APP_SECRET:
            problems.append(
                "WHATSAPP_APP_SECRET is not set - inbound webhook signatures cannot be "
                "verified (acceptable for local testing only)"
            )

    return (not problems, problems)


def build_clients(platforms: Optional[List[Platform]] = None) -> Dict[Platform, MessagingClient]:
    """Instantiate one client per enabled platform."""
    platforms = platforms or enabled_platforms()
    ok, problems = validate_platform_config(platforms)

    # A missing app secret degrades security but still runs; anything else is fatal.
    fatal = [p for p in problems if "APP_SECRET" not in p]
    if fatal:
        raise PlatformConfigError(
            "Messaging configuration is incomplete:\n  - " + "\n  - ".join(fatal)
        )
    for warning in problems:
        if warning not in fatal:
            logger.warning(warning)

    clients: Dict[Platform, MessagingClient] = {}

    if Platform.TELEGRAM in platforms:
        from telegram import Bot
        from telegram.request import HTTPXRequest

        from messaging.telegram_client import TelegramClient

        bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN,
            request=HTTPXRequest(connection_pool_size=16, read_timeout=30, write_timeout=30),
        )
        clients[Platform.TELEGRAM] = TelegramClient(bot)
        logger.info("Telegram client ready")

    if Platform.WHATSAPP in platforms:
        from messaging.whatsapp_client import WhatsAppClient

        clients[Platform.WHATSAPP] = WhatsAppClient(
            access_token=settings.WHATSAPP_ACCESS_TOKEN,
            phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
            api_base=settings.WHATSAPP_API_BASE,
            api_version=settings.WHATSAPP_API_VERSION,
            timeout=settings.WHATSAPP_REQUEST_TIMEOUT,
        )
        logger.info(
            f"WhatsApp client ready (phone_number_id={settings.WHATSAPP_PHONE_NUMBER_ID}, "
            f"api={settings.WHATSAPP_API_VERSION})"
        )

    return clients


def build_router(platforms: Optional[List[Platform]] = None) -> MessagingRouter:
    """Build the router for the platforms selected by the feature flag."""
    return MessagingRouter(build_clients(platforms))


def build_router_from_telegram_bot(bot) -> MessagingRouter:
    """
    Build a Telegram-only router around an existing Bot instance.

    Used by python-telegram-bot's Application, which owns its own Bot object.
    """
    from messaging.telegram_client import TelegramClient

    return MessagingRouter({Platform.TELEGRAM: TelegramClient(bot)})
