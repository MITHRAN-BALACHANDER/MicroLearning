"""
Configuration settings for the MicroLearning Bot
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# Messaging platform feature flag
# ---------------------------------------------------------------------------
# MESSAGING_PLATFORM controls which channels the application runs on:
#   telegram          -> Telegram only (default, existing behaviour)
#   whatsapp          -> WhatsApp Cloud API only
#   both / all        -> both channels at once
#   telegram,whatsapp -> explicit comma-separated list (same as "both")
MESSAGING_PLATFORM = os.getenv("MESSAGING_PLATFORM", "telegram").strip().lower()


def _parse_platforms(value: str) -> tuple:
    """Turn the MESSAGING_PLATFORM value into a tuple of platform names."""
    if value in ("both", "all", "*"):
        return ("telegram", "whatsapp")

    names = []
    for raw in value.replace("+", ",").split(","):
        name = raw.strip()
        if not name:
            continue
        if name not in ("telegram", "whatsapp"):
            raise ValueError(
                f"Unknown messaging platform '{name}' in MESSAGING_PLATFORM='{value}'. "
                f"Valid values: telegram, whatsapp, both"
            )
        if name not in names:
            names.append(name)

    if not names:
        raise ValueError("MESSAGING_PLATFORM is empty. Valid values: telegram, whatsapp, both")
    return tuple(names)


ENABLED_PLATFORMS = _parse_platforms(MESSAGING_PLATFORM)
TELEGRAM_ENABLED = "telegram" in ENABLED_PLATFORMS
WHATSAPP_ENABLED = "whatsapp" in ENABLED_PLATFORMS

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ---------------------------------------------------------------------------
# WhatsApp Cloud API Configuration (Meta Graph API)
# ---------------------------------------------------------------------------
# Permanent system-user token with whatsapp_business_messaging scope
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
# "Phone number ID" from Meta -> WhatsApp -> API Setup (NOT the phone number itself)
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
# WhatsApp Business Account ID (used for template management / diagnostics)
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
# Self-chosen string; must match what you type into Meta's webhook config screen
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
# App secret from Meta -> App Settings -> Basic; used for X-Hub-Signature-256
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")
WHATSAPP_API_BASE = os.getenv("WHATSAPP_API_BASE", "https://graph.facebook.com").rstrip("/")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")
WHATSAPP_REQUEST_TIMEOUT = float(os.getenv("WHATSAPP_REQUEST_TIMEOUT", "30"))
# Approved template used to re-open a conversation outside the 24h service window
WHATSAPP_TEMPLATE_DAILY_VIDEO = os.getenv("WHATSAPP_TEMPLATE_DAILY_VIDEO", "daily_video_ready")
WHATSAPP_TEMPLATE_LANGUAGE = os.getenv("WHATSAPP_TEMPLATE_LANGUAGE", "en_US")

# Webhook server (WhatsApp inbound messages + /health)
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))
WHATSAPP_WEBHOOK_PATH = os.getenv("WHATSAPP_WEBHOOK_PATH", "/webhook/whatsapp")

# Upload a video to a platform automatically the first time it is requested
AUTO_UPLOAD_MEDIA = _env_flag("AUTO_UPLOAD_MEDIA", "true")

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Agno Configuration
AGNO_API_KEY = os.getenv("AGNO_API_KEY")
AGNO_ENV = os.getenv("AGNO_ENV", "development")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./microlearning.db")

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")

# Admin Dashboard Configuration
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Agent Configuration
DAILY_VIDEO_TIME = os.getenv("DAILY_VIDEO_TIME", "09:00")
VIDEO_BATCH_SIZE = int(os.getenv("VIDEO_BATCH_SIZE", "1"))
QUESTION_TIMEOUT = int(os.getenv("QUESTION_TIMEOUT", "300"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "./logs/bot.log")

# Paths
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
# Override with VIDEOS_DIR when running in Docker / Linux
VIDEOS_DIR = Path(os.getenv("VIDEOS_DIR", "C:/MicroLearning/data/videos"))
LOGS_DIR = BASE_DIR / "logs"

# Admin Configuration
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "6437411483")  # Mithran's ID
# Telegram has no standalone media upload endpoint, so uploads are staged
# through this chat to obtain a reusable file_id.
TELEGRAM_UPLOAD_STAGING_CHAT_ID = os.getenv("TELEGRAM_UPLOAD_STAGING_CHAT_ID", ADMIN_CHAT_ID)

# Create directories if they don't exist
for directory in [DATA_DIR, DOCUMENTS_DIR, VIDEOS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Agent Prompts
VIDEO_AGENT_PROMPT = """
You are a Video Sending Agent responsible for managing daily video delivery to users.
Your tasks include:
1. Selecting appropriate videos based on user progress
2. Tracking viewing history
3. Ensuring progressive learning paths
4. Personalizing content delivery

Be friendly and encouraging in your communications.
"""

QUESTION_AGENT_PROMPT = """
You are a Question & Rating Agent that creates conceptual questions based on video content.
Your responsibilities:
1. Generate relevant questions from video transcripts and metadata
2. Evaluate user answers accurately and fairly
3. Provide constructive feedback
4. Rate answers on a scale of 0-10
5. Track learning progress

Be objective but encouraging. Focus on understanding, not memorization.
"""

RAG_AGENT_PROMPT = """
You are a RAG Agent with access to company manuals and SOPs.
Your role:
1. Answer questions about company policies and procedures
2. Retrieve relevant documentation
3. Provide accurate, sourced information
4. Summarize complex documents

Always cite your sources and be precise in your answers.
"""
