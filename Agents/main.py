"""
Main entry point - MicroLearning with Multiple Agno Agents

Which messaging channels run is decided by the MESSAGING_PLATFORM environment
flag (telegram | whatsapp | both). All learner-facing behaviour lives in
CommandDispatcher, so both channels behave identically.
"""
import os
import sys
import time
import warnings

# Suppress warnings for cleaner logs
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message='resume_download')
os.environ['ANONYMIZED_TELEMETRY'] = 'False'  # Disable ChromaDB telemetry

from loguru import logger

from config.settings import (
    LOG_FILE,
    LOG_LEVEL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ENABLED,
    WHATSAPP_ENABLED,
    ENABLED_PLATFORMS,
    WEBHOOK_HOST,
    WEBHOOK_PORT,
    WHATSAPP_WEBHOOK_PATH,
)
from database.operations import init_db
from agents.orchestrator import AgentOrchestrator
from dispatcher import CommandDispatcher, Profile
from messaging.base import Platform, UserRef
from messaging.factory import (
    PlatformConfigError,
    build_clients,
    enabled_platforms,
    validate_platform_config,
)
from messaging.router import MessagingRouter
from messaging.worker import AsyncWorker

# Configure logging
logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)
logger.add(LOG_FILE, rotation="1 day", retention="7 days", level=LOG_LEVEL)


class MicroLearningBot:
    """Boots the agents and every messaging channel enabled by the flag."""

    def __init__(self):
        self.router = None
        self.orchestrator = None
        self.dispatcher = None
        self.telegram_app = None
        self.worker = None
        logger.info("Initializing MicroLearning Bot...")

    # -- setup ------------------------------------------------------------

    def build(self):
        """Create the messaging clients, agents, and dispatcher."""
        logger.info(f"Enabled platforms: {', '.join(ENABLED_PLATFORMS)}")

        ok, problems = validate_platform_config()
        for problem in problems:
            logger.warning(problem)
        fatal = [p for p in problems if "APP_SECRET" not in p]
        if fatal:
            raise PlatformConfigError(
                "Messaging configuration is incomplete:\n  - " + "\n  - ".join(fatal)
            )

        # python-telegram-bot owns its own Bot instance, so the Application is
        # built here and its bot is wrapped for the router; other platforms are
        # built by the factory.
        clients = build_clients(
            [p for p in enabled_platforms() if p is not Platform.TELEGRAM]
        )

        if TELEGRAM_ENABLED:
            from telegram.ext import Application

            from messaging.telegram_client import TelegramClient

            self.telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            clients[Platform.TELEGRAM] = TelegramClient(self.telegram_app.bot)

        self.router = MessagingRouter(clients)
        self.orchestrator = AgentOrchestrator(self.router)
        self.dispatcher = CommandDispatcher(self.orchestrator)

        if TELEGRAM_ENABLED:
            self.register_telegram_handlers()

        logger.info(f"Agent status: {self.orchestrator.get_all_agents_status()}")

    # -- telegram ---------------------------------------------------------

    def register_telegram_handlers(self):
        """Thin Telegram handlers that delegate to the shared dispatcher."""
        from telegram import Update
        from telegram.ext import CommandHandler, MessageHandler, filters

        logger.info("Registering Telegram command handlers...")

        def command(name):
            async def handler(update, context):
                ref, profile = _telegram_identity(update)
                args = " ".join(context.args) if context.args else ""
                await self.dispatcher.run_command(ref, name, args, profile)
            return handler

        for name in ("start", "video", "quiz", "ask", "progress", "docs", "help"):
            self.telegram_app.add_handler(CommandHandler(name, command(name)))

        async def on_message(update, context):
            ref, profile = _telegram_identity(update)
            self.dispatcher.register_inbound(ref, profile)
            await self.dispatcher.handle_text(ref, update.message.text, profile)

        self.telegram_app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, on_message)
        )

        async def on_error(update, context):
            logger.error(f"Update {update} caused error {context.error}")
            if update and getattr(update, "effective_message", None):
                await update.effective_message.reply_text(
                    "ERROR: An error occurred. Please try again or contact support."
                )

        self.telegram_app.add_error_handler(on_error)

    # -- whatsapp ---------------------------------------------------------

    def build_webhook_app(self):
        """Create the Flask app serving the WhatsApp webhook and /health."""
        from whatsapp_webhook import create_app

        self.worker = AsyncWorker(name="whatsapp-worker").start()
        return create_app(
            dispatcher=self.dispatcher,
            worker=self.worker,
            orchestrator=self.orchestrator,
        )

    # -- run --------------------------------------------------------------

    def run(self):
        """Start every enabled channel."""
        try:
            logger.info("Initializing database...")
            init_db()
            logger.info("Database initialized successfully")

            self.build()

            logger.info("=" * 60)
            logger.info("MicroLearning Bot is READY!")
            logger.info(f"Channels: {', '.join(ENABLED_PLATFORMS)}")
            logger.info("=" * 60)

            # The HTTP server always runs: it serves /health for container and
            # deploy probes, and the WhatsApp callback when that channel is on.
            if TELEGRAM_ENABLED:
                self._serve_http_in_background()
                self._run_telegram_polling()
            else:
                self._serve_http_in_foreground()

        except PlatformConfigError as e:
            logger.error(str(e))
            raise
        except KeyboardInterrupt:
            logger.info("\nBot stopped by user")
        except Exception as e:
            logger.error(f"Failed to start: {str(e)}")
            logger.exception(e)
            raise
        finally:
            if self.worker is not None:
                self.worker.stop()

    def _log_http_endpoints(self):
        logger.info(f"HTTP server on {WEBHOOK_HOST}:{WEBHOOK_PORT} (health: /health)")
        if WHATSAPP_ENABLED:
            logger.info(
                f"WhatsApp callback URL: https://<your-public-domain>{WHATSAPP_WEBHOOK_PATH} "
                f"-> {WEBHOOK_HOST}:{WEBHOOK_PORT}{WHATSAPP_WEBHOOK_PATH}"
            )

    def _warm_up_agents(self):
        """
        Build the agents in the background once the server is listening.

        Loading sentence-transformers/torch takes minutes on a cold start, so
        this happens after the port is bound rather than before: Meta's webhook
        verification and health probes stay responsive, and the first learner
        message does not pay the full cost.
        """
        import threading

        def warm():
            logger.info("Warming up agents in the background...")
            started = time.time()
            self.orchestrator.warm_up()
            logger.info(f"Agents ready ({time.time() - started:.0f}s)")

        threading.Thread(target=warm, name="agent-warmup", daemon=True).start()

    def _run_telegram_polling(self):
        from telegram import Update

        logger.info("Starting Telegram polling...")
        self.telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)

    def _serve_http_in_foreground(self):
        from whatsapp_webhook import run_webhook_server

        app = self.build_webhook_app()
        self._log_http_endpoints()
        self._warm_up_agents()
        run_webhook_server(app, WEBHOOK_HOST, WEBHOOK_PORT)

    def _serve_http_in_background(self):
        """Run the HTTP server on a daemon thread alongside Telegram polling."""
        import threading

        from whatsapp_webhook import run_webhook_server

        app = self.build_webhook_app()
        threading.Thread(
            target=run_webhook_server,
            args=(app, WEBHOOK_HOST, WEBHOOK_PORT),
            name="webhook-server",
            daemon=True,
        ).start()
        self._log_http_endpoints()
        self._warm_up_agents()


def _telegram_identity(update):
    """Build a UserRef + Profile from a Telegram update."""
    user = update.effective_user
    ref = UserRef(Platform.TELEGRAM, str(user.id))
    profile = Profile(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    return ref, profile


if __name__ == "__main__":
    try:
        bot = MicroLearningBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
