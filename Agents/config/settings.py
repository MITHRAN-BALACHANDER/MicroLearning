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

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Agno Configuration
AGNO_API_KEY = os.getenv("AGNO_API_KEY")
AGNO_ENV = os.getenv("AGNO_ENV", "development")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./microlearning.db")

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")

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
VIDEOS_DIR = DATA_DIR / "videos"
LOGS_DIR = BASE_DIR / "logs"

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
