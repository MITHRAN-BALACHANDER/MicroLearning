"""
CommandDispatcher - platform-agnostic command handling.

Every learner-facing behaviour lives here exactly once. The Telegram handlers
in main.py and the WhatsApp webhook both call into this class, so the two
channels can never drift apart.

WhatsApp has no native slash-command UI, so bare keywords ("video", "quiz")
are accepted alongside the slash forms. Telegram keeps its native commands and
behaves exactly as before.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

from agents.orchestrator import AgentType
from database.operations import get_or_create_user_from_ref
from messaging.base import UserRef

WELCOME_TEMPLATE = """Welcome to MicroLearning Bot, {name}!

I'm powered by multiple AI agents to help you learn effectively:

- Video Agent - Delivers daily learning videos
- Question Agent - Tests your understanding
- RAG Agent - Answers questions from company docs

Available Commands:
/video - Get today's learning video
/quiz - Take a quiz on recent content
/ask [question] - Ask about company manuals/SOPs
/progress - View your learning progress
/docs - List available documents
/help - Show this help message

Let's start your learning journey!"""

HELP_TEXT = """MicroLearning Bot Help

Commands:

/video - Get your next learning video

/quiz - Start a quiz on recent content
   After watching a video, test your understanding!

/ask [question] - Ask about company documents
   Example: /ask What is the remote work policy?

/docs - List all available documents
   See what manuals and SOPs are available

/progress - View your learning statistics
   Track your videos watched and quiz scores

How it works:

1. Daily Videos - Request a video with /video
2. Take Quizzes - After watching, use /quiz
3. Ask Questions - Use /ask for company info

Agents:
- Video Agent - Manages content delivery
- Question Agent - Creates and evaluates quizzes
- RAG Agent - Answers questions from documents

Need more help? Contact your administrator."""

FALLBACK_HINT = """I'll help you with that! Use one of these commands:

- /video for your next video
- /quiz for a quiz
- /ask [question] to search company documents
- /progress for your stats
- /help for everything"""

# Bare words accepted as commands (WhatsApp has no slash-command menu)
BARE_COMMANDS = {
    "start", "hi", "hello", "menu",
    "video", "quiz", "ask", "progress", "docs", "help",
}

COMMAND_ALIASES = {
    "hi": "start",
    "hello": "start",
    "menu": "help",
}


@dataclass
class Profile:
    """Optional display details supplied by the platform."""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @property
    def display_name(self) -> str:
        return self.first_name or self.username or "there"


@dataclass
class ParsedCommand:
    command: Optional[str]
    args: str
    is_explicit: bool  # True when the user typed a leading '/'


def parse_command(text: str, *, allow_bare: bool) -> ParsedCommand:
    """
    Turn raw message text into a command + arguments.

    `allow_bare` lets WhatsApp users type "video" instead of "/video"; it is
    False mid-quiz so an answer is never mistaken for a command.
    """
    stripped = (text or "").strip()
    if not stripped:
        return ParsedCommand(None, "", False)

    if stripped.startswith("/"):
        parts = stripped[1:].split(maxsplit=1)
        if not parts:
            return ParsedCommand(None, "", False)
        name = parts[0].lower()
        # Telegram sends "/video@BotName" in groups
        name = name.split("@", 1)[0]
        return ParsedCommand(COMMAND_ALIASES.get(name, name), parts[1] if len(parts) > 1 else "", True)

    if allow_bare:
        parts = stripped.split(maxsplit=1)
        name = parts[0].lower()
        if name in BARE_COMMANDS:
            return ParsedCommand(COMMAND_ALIASES.get(name, name), parts[1] if len(parts) > 1 else "", False)

    return ParsedCommand(None, stripped, False)


class CommandDispatcher:
    """Executes learner commands for any platform."""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.router = orchestrator.router

    # -- entry point ------------------------------------------------------

    async def handle_text(self, ref: UserRef, text: str,
                          profile: Optional[Profile] = None) -> Dict[str, Any]:
        """
        Handle one inbound text message end to end.

        Returns a small result dict for logging/tests; user-visible output is
        sent through the messaging router.
        """
        profile = profile or Profile()
        # Asking the orchestrator avoids building the question agent just to
        # discover that this learner is not in a quiz.
        in_quiz = self.orchestrator.has_active_quiz(ref)

        parsed = parse_command(text, allow_bare=not in_quiz)

        try:
            # Explicit slash commands always win, even mid-quiz (Telegram parity)
            if parsed.command:
                return await self.run_command(ref, parsed.command, parsed.args, profile)

            if in_quiz:
                question_agent = await self.orchestrator.get_agent(AgentType.QUESTION)
                await question_agent.evaluate_answer(ref, text.strip())
                return {"success": True, "handled_as": "quiz_answer"}

            return await self.handle_freeform(ref, text)

        except Exception:
            logger.exception(f"Error handling message from {ref}")
            await self.router.send_message(
                ref, "ERROR: An error occurred. Please try again or contact support."
            )
            return {"success": False, "handled_as": "error"}

    async def run_command(self, ref: UserRef, command: str, args: str,
                          profile: Optional[Profile] = None) -> Dict[str, Any]:
        """Dispatch a single named command."""
        profile = profile or Profile()

        handlers = {
            "start": lambda: self.cmd_start(ref, profile),
            "video": lambda: self.cmd_video(ref),
            "quiz": lambda: self.cmd_quiz(ref),
            "ask": lambda: self.cmd_ask(ref, args),
            "progress": lambda: self.cmd_progress(ref),
            "docs": lambda: self.cmd_docs(ref),
            "help": lambda: self.cmd_help(ref),
        }

        handler = handlers.get(command)
        if handler is None:
            await self.router.send_message(
                ref, f"Unknown command '/{command}'.\n\n{FALLBACK_HINT}"
            )
            return {"success": False, "handled_as": "unknown_command"}

        result = await handler()
        return result if isinstance(result, dict) else {"success": True, "handled_as": command}

    # -- commands ---------------------------------------------------------

    async def cmd_start(self, ref: UserRef, profile: Profile) -> Dict[str, Any]:
        """Register the learner and send the welcome message."""
        get_or_create_user_from_ref(
            ref,
            username=profile.username,
            first_name=profile.first_name,
            last_name=profile.last_name,
        )
        await self.router.send_message(ref, WELCOME_TEMPLATE.format(name=profile.display_name))
        logger.info(f"User registered: {ref} on {ref.platform.value}")
        return {"success": True, "handled_as": "start"}

    async def cmd_video(self, ref: UserRef) -> Dict[str, Any]:
        await self.router.send_message(ref, "Fetching your next video...")

        video_agent = await self.orchestrator.get_agent(AgentType.VIDEO)
        result = await video_agent.send_daily_video(ref)

        if not result["success"]:
            error_msg = result.get("error", "Unknown error occurred")
            await self.router.send_message(ref, f"ERROR: {error_msg}")
            logger.error(f"Video command failed for {ref}: {error_msg}")

        return {"success": result["success"], "handled_as": "video"}

    async def cmd_quiz(self, ref: UserRef) -> Dict[str, Any]:
        await self.router.send_message(ref, "Preparing your quiz...")

        question_agent = await self.orchestrator.get_agent(AgentType.QUESTION)
        result = await question_agent.start_quiz(ref)

        if not result["success"]:
            error_msg = result.get("error", "Unable to start quiz")
            await self.router.send_message(ref, f"ERROR: {error_msg}")
            logger.error(f"Quiz command failed for {ref}: {error_msg}")

        return {"success": result["success"], "handled_as": "quiz"}

    async def cmd_ask(self, ref: UserRef, query: str) -> Dict[str, Any]:
        if not query.strip():
            await self.router.send_message(
                ref,
                "Please provide a question.\n\nExample: /ask What is the vacation policy?"
            )
            return {"success": False, "handled_as": "ask_missing_query"}

        await self.router.send_message(ref, "Searching company documents...")

        rag_agent = await self.orchestrator.get_agent(AgentType.RAG)
        result = await rag_agent.query_documents(query, ref)

        if not result["success"]:
            await self.router.send_message(
                ref, f"ERROR: {result.get('error', 'Unknown error occurred')}"
            )

        return {"success": result["success"], "handled_as": "ask"}

    async def cmd_progress(self, ref: UserRef) -> Dict[str, Any]:
        video_agent = await self.orchestrator.get_agent(AgentType.VIDEO)
        result = await video_agent.get_user_video_progress(ref)

        if not result["success"]:
            await self.router.send_message(ref, f"ERROR: {result['error']}")
            return {"success": False, "handled_as": "progress"}

        progress = result["progress"]
        await self.router.send_message(
            ref,
            f"Your Learning Progress\n\n"
            f"Videos:\n"
            f"  - Watched: {progress['watched_videos']}/{progress['total_videos']}\n"
            f"  - Completion: {progress['completion_rate']:.1f}%\n\n"
            f"Quizzes:\n"
            f"  - Questions Answered: {progress['total_questions_answered']}\n"
            f"  - Average Score: {progress['average_score']}/10\n\n"
            f"Keep up the great work!"
        )
        return {"success": True, "handled_as": "progress"}

    async def cmd_docs(self, ref: UserRef) -> Dict[str, Any]:
        rag_agent = await self.orchestrator.get_agent(AgentType.RAG)
        await rag_agent.list_available_documents(ref)
        return {"success": True, "handled_as": "docs"}

    async def cmd_help(self, ref: UserRef) -> Dict[str, Any]:
        await self.router.send_message(ref, HELP_TEXT)
        return {"success": True, "handled_as": "help"}

    # -- free text --------------------------------------------------------

    async def handle_freeform(self, ref: UserRef, text: str) -> Dict[str, Any]:
        """Route non-command text through the orchestrator and nudge the user."""
        result = await self.orchestrator.process_message(ref, text)
        if result["success"]:
            await self.router.send_message(ref, FALLBACK_HINT)
        return {"success": result["success"], "handled_as": "freeform"}

    async def handle_unsupported(self, ref: UserRef, message_type: str) -> Dict[str, Any]:
        """Reply to stickers, images, audio and other non-text payloads."""
        await self.router.send_message(
            ref,
            f"I can only read text messages right now (received: {message_type}).\n\n{FALLBACK_HINT}"
        )
        return {"success": True, "handled_as": "unsupported"}

    # -- registration -----------------------------------------------------

    def register_inbound(self, ref: UserRef, profile: Optional[Profile] = None) -> None:
        """
        Record an inbound message.

        For WhatsApp this timestamp defines the 24-hour customer service window
        during which free-form replies are allowed.
        """
        profile = profile or Profile()
        try:
            get_or_create_user_from_ref(
                ref,
                username=profile.username,
                first_name=profile.first_name,
                last_name=profile.last_name,
                touch_inbound=True,
            )
        except Exception:
            logger.exception(f"Could not record inbound message for {ref}")
