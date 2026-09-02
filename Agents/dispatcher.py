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
from messaging.base import Choice, UserRef
from messaging.formatting import DIVIDER, bold, bullets, italic, paragraphs

# ---------------------------------------------------------------------------
# Learner-facing copy
# ---------------------------------------------------------------------------
# Formatted with WhatsApp's syntax (see messaging.formatting): *bold*, _italic_,
# "- " bullets. Telegram parses the same markers.
#
# Written to a few rules that matter more on a phone than on a screen:
# - lead with the value, not the feature list
# - one idea per message; the menu carries the options
# - errors say what failed, why, and what to do next - never a code
# - empty states name what becomes possible, not what is missing
#
# The word is "lesson", never "video". A lesson arrives as video, audio, a
# document, or a short read, and the learner picks it from one menu either way.

WELCOME_TEMPLATE = """*Welcome to MicroLearning, {name}*

- Short lessons - watch, listen, or read
- A few questions to check what stuck
- Straight answers from your company's documents

_About five minutes a day._"""

MENU_PROMPT = "What would you like to do?"
MENU_HEADER = "MicroLearning"
MENU_FOOTER = "Tap an option below"

# The menu a learner actually taps. `id` must match a command name in
# run_command(); `title` is the label. WhatsApp shows up to 3 of these as
# buttons and anything larger as a list, so six entries stay one tap away.
MAIN_MENU = [
    Choice("lesson", "Next lesson", "Watch, listen or read"),
    Choice("quiz", "Take a quiz", "Check what stuck"),
    Choice("ask", "Ask a question", "Search company documents"),
    Choice("progress", "My progress", "Lessons done and scores"),
    Choice("docs", "Library", "Everything you can search"),
    Choice("help", "How this works", "A one-minute explainer"),
]

# Three or fewer, so these render as real buttons rather than a list.
AFTER_LESSON_MENU = [
    Choice("quiz", "Take the quiz"),
    Choice("lesson", "Next lesson"),
    Choice("menu", "Main menu"),
]

AFTER_QUIZ_MENU = [
    Choice("lesson", "Next lesson"),
    Choice("progress", "My progress"),
    Choice("menu", "Main menu"),
]

# Offered when there is nothing to show yet - one clear next action.
START_LEARNING_MENU = [
    Choice("lesson", "Start first lesson"),
    Choice("menu", "Main menu"),
]

HELP_TEXT = """*How this works*

1. *Learn* - a short lesson: watch a video, listen, or read
2. *Answer* - a few questions, scored out of 10 with feedback
3. *Ask* - anything covered by your company's handbooks

_You can also type: lesson, quiz, ask, progress, library_"""

ASK_PROMPT = """*Ask a question*

Send it as a normal message and I'll search your company's documents.

_For example: What is the leave policy?_"""

# Errors: what failed, then what to do. No codes, no blame, and a word on
# whether their work survived - that is the actual worry mid-quiz.
GENERIC_ERROR = """*Something went wrong on our end*

Your progress is saved. Try again in a moment."""

UNSUPPORTED_TEMPLATE = """*I can only read text right now*

Send your message as text, or tap an option below.

_Received: {message_type}_"""

# Bare words accepted as commands (WhatsApp has no slash-command menu)
BARE_COMMANDS = {
    "start", "hi", "hello", "menu",
    "lesson", "video", "watch", "listen", "read",
    "quiz", "ask", "progress", "docs", "library", "help",
}

# A learner types what they want to do, not what we called the handler.
# "video" is kept because it is what the Telegram slash menu has always
# offered and old links still use it.
COMMAND_ALIASES = {
    "hi": "start",
    "hello": "start",
    "video": "lesson",
    "watch": "lesson",
    "listen": "lesson",
    "read": "lesson",
    "library": "docs",
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
    is_explicit: bool # True when the user typed a leading '/'


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
        # Learners who tapped "Ask a question" and whose next plain message
        # should therefore go to the RAG agent instead of the generic router.
        # In-memory on purpose: a restart should drop the prompt rather than
        # resurrect it hours later against an unrelated message.
        self._awaiting_question = set()

    # -- entry point ------------------------------------------------------

    async def handle_text(self, ref: UserRef, text: str,
                          profile: Optional[Profile] = None,
                          *, from_button: bool = False) -> Dict[str, Any]:
        """
        Handle one inbound text message end to end.

        `from_button` marks a tap on an interactive menu, where `text` is the
        choice id rather than something the learner typed. Those are always
        commands - without this, tapping "Take a quiz" mid-quiz would get
        "quiz" graded as the learner's answer.

        Returns a small result dict for logging/tests; user-visible output is
        sent through the messaging router.
        """
        profile = profile or Profile()
        # Asking the orchestrator avoids building the question agent just to
        # discover that this learner is not in a quiz.
        in_quiz = self.orchestrator.has_active_quiz(ref)

        if from_button:
            parsed = parse_command(text, allow_bare=True)
            if parsed.command is None:
                # An id we do not recognise: show the menu rather than guess.
                parsed = ParsedCommand("menu", "", False)
        else:
            parsed = parse_command(text, allow_bare=not in_quiz)

        try:
            # Explicit slash commands always win, even mid-quiz (Telegram parity)
            if parsed.command:
                self._awaiting_question.discard(ref.key)
                return await self.run_command(ref, parsed.command, parsed.args, profile)

            if in_quiz:
                question_agent = await self.orchestrator.get_agent(AgentType.QUESTION)
                outcome = await question_agent.evaluate_answer(ref, text.strip())

                if isinstance(outcome, dict) and outcome.get("quiz_completed"):
                    await self.router.send_choices(
                        ref, "What next?", AFTER_QUIZ_MENU, list_label="Options"
                    )

                return {"success": True, "handled_as": "quiz_answer"}

            if ref.key in self._awaiting_question:
                self._awaiting_question.discard(ref.key)
                return await self.cmd_ask(ref, text)

            return await self.handle_freeform(ref, text)

        except Exception:
            logger.exception(f"Error handling message from {ref}")
            await self.router.send_message(ref, GENERIC_ERROR)
            return {"success": False, "handled_as": "error"}

    async def run_command(self, ref: UserRef, command: str, args: str,
                          profile: Optional[Profile] = None) -> Dict[str, Any]:
        """Dispatch a single named command."""
        profile = profile or Profile()

        handlers = {
            "start": lambda: self.cmd_start(ref, profile),
            "lesson": lambda: self.cmd_lesson(ref),
            "quiz": lambda: self.cmd_quiz(ref),
            "ask": lambda: self.cmd_ask(ref, args),
            "progress": lambda: self.cmd_progress(ref),
            "docs": lambda: self.cmd_docs(ref),
            "help": lambda: self.cmd_help(ref),
            "menu": lambda: self.cmd_menu(ref),
        }

        handler = handlers.get(command)
        if handler is None:
            await self.send_menu(ref, f"I do not know how to do that.")
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
        await self.send_menu(ref)
        logger.info(f"User registered: {ref} on {ref.platform.value}")
        return {"success": True, "handled_as": "start"}

    async def cmd_lesson(self, ref: UserRef) -> Dict[str, Any]:
        """Deliver the learner's next lesson, whatever format it arrives in."""
        await self.router.send_message(ref, italic("Finding your next lesson..."))

        video_agent = await self.orchestrator.get_agent(AgentType.VIDEO)
        result = await video_agent.send_daily_video(ref)

        if not result["success"]:
            error_msg = result.get("error", "")
            logger.error(f"Lesson command failed for {ref}: {error_msg}")
            await self.router.send_message(
                ref,
                paragraphs(
                    bold("Couldn't load your next lesson"),
                    error_msg or "Something interrupted the download.",
                    italic("Nothing was lost - try again in a moment."),
                ),
            )
            await self.send_menu(ref)
        else:
            await self.router.send_choices(
                ref,
                "Finished with that one?",
                AFTER_LESSON_MENU,
                footer="Quizzes are scored out of 10",
                list_label="Options",
            )

        return {"success": result["success"], "handled_as": "lesson"}

    async def cmd_quiz(self, ref: UserRef) -> Dict[str, Any]:
        await self.router.send_message(ref, italic("Writing your questions..."))

        question_agent = await self.orchestrator.get_agent(AgentType.QUESTION)
        result = await question_agent.start_quiz(ref)

        if not result["success"]:
            error_msg = result.get("error", "")
            logger.error(f"Quiz command failed for {ref}: {error_msg}")

            if result.get("needs_video"):
                # Empty state, not a failure: say what unlocks it.
                await self.router.send_choices(
                    ref,
                    paragraphs(
                        bold("No quiz ready yet"),
                        "Finish a lesson first and I'll build questions from it.",
                    ),
                    START_LEARNING_MENU,
                    list_label="Options",
                )
            else:
                await self.router.send_message(
                    ref,
                    paragraphs(
                        bold("Couldn't start your quiz"),
                        error_msg or "The questions didn't come back in time.",
                        italic("Try again in a moment."),
                    ),
                )
                await self.send_menu(ref)

        return {"success": result["success"], "handled_as": "quiz"}

    async def cmd_ask(self, ref: UserRef, query: str) -> Dict[str, Any]:
        if not query.strip():
            # Tapping "Ask a question" carries no text, so prompt and route the
            # learner's next plain message to the RAG agent.
            self._awaiting_question.add(ref.key)
            await self.router.send_message(ref, ASK_PROMPT)
            return {"success": True, "handled_as": "ask_prompt"}

        await self.router.send_message(ref, italic("Searching your documents..."))

        rag_agent = await self.orchestrator.get_agent(AgentType.RAG)
        result = await rag_agent.query_documents(query, ref)

        if not result["success"]:
            await self.router.send_message(
                ref,
                paragraphs(
                    bold("Couldn't search the documents"),
                    result.get("error", "") or "The search didn't come back in time.",
                    italic("Try rewording your question, or ask again shortly."),
                ),
            )

        await self.send_menu(ref, "Anything else?")
        return {"success": result["success"], "handled_as": "ask"}

    async def cmd_progress(self, ref: UserRef) -> Dict[str, Any]:
        video_agent = await self.orchestrator.get_agent(AgentType.VIDEO)
        result = await video_agent.get_user_video_progress(ref)

        if not result["success"]:
            await self.router.send_message(
                ref,
                paragraphs(
                    bold("Couldn't load your progress"),
                    italic("Your scores are safe. Try again in a moment."),
                ),
            )
            return {"success": False, "handled_as": "progress"}

        progress = result["progress"]

        if not progress["watched_videos"] and not progress["total_questions_answered"]:
            # First-use empty state: name what starts it, not what is missing.
            await self.router.send_choices(
                ref,
                paragraphs(
                    bold("No progress yet"),
                    "Finish your first lesson and your scores will show up here.",
                ),
                START_LEARNING_MENU,
                list_label="Options",
            )
            return {"success": True, "handled_as": "progress"}

        await self.router.send_message(
            ref,
            paragraphs(
                bold("Your progress"),
                paragraphs(
                    bold("Lessons"),
                    bullets([
                        f"{progress['watched_videos']} of {progress['total_videos']} done",
                        f"{progress['completion_rate']:.0f}% complete",
                    ]),
                ),
                paragraphs(
                    bold("Quizzes"),
                    bullets([
                        f"{progress['total_questions_answered']} questions answered",
                        f"Average score {progress['average_score']}/10",
                    ]),
                ),
            ),
        )
        await self.send_menu(ref, "Anything else?")
        return {"success": True, "handled_as": "progress"}

    async def cmd_docs(self, ref: UserRef) -> Dict[str, Any]:
        rag_agent = await self.orchestrator.get_agent(AgentType.RAG)
        await rag_agent.list_available_documents(ref)
        await self.send_menu(ref, "Anything else?")
        return {"success": True, "handled_as": "docs"}

    async def cmd_help(self, ref: UserRef) -> Dict[str, Any]:
        await self.router.send_message(ref, HELP_TEXT)
        await self.send_menu(ref)
        return {"success": True, "handled_as": "help"}

    async def cmd_menu(self, ref: UserRef) -> Dict[str, Any]:
        await self.send_menu(ref)
        return {"success": True, "handled_as": "menu"}

    # -- menus ------------------------------------------------------------

    async def send_menu(self, ref: UserRef, prompt: Optional[str] = None) -> None:
        """Show the main menu. Defined once, so no channel drifts from another."""
        await self.router.send_choices(
            ref,
            prompt or MENU_PROMPT,
            MAIN_MENU,
            header=MENU_HEADER,
            footer=MENU_FOOTER,
            list_label="Show options",
        )

    # -- free text --------------------------------------------------------

    async def handle_freeform(self, ref: UserRef, text: str) -> Dict[str, Any]:
        """Route non-command text through the orchestrator and nudge the user."""
        result = await self.orchestrator.process_message(ref, text)
        if result["success"]:
            await self.send_menu(ref)
        return {"success": result["success"], "handled_as": "freeform"}

    async def handle_unsupported(self, ref: UserRef, message_type: str) -> Dict[str, Any]:
        """Reply to stickers, images, audio and other non-text payloads."""
        await self.send_menu(
            ref, UNSUPPORTED_TEMPLATE.format(message_type=message_type)
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
