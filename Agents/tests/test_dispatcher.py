"""
Tests for the shared command dispatcher.

The point of these is parity: a Telegram user and a WhatsApp user issuing the
same command must travel the same code path and get the same behaviour.
"""
import pytest

from dispatcher import CommandDispatcher, Profile, parse_command
from messaging.base import Platform, UserRef


class FakeQuestionAgent:
    def __init__(self):
        self.active = set()
        self.started = []
        self.evaluated = []

    def has_active_quiz(self, ref):
        return ref.key in self.active

    async def start_quiz(self, ref):
        self.started.append(ref)
        self.active.add(ref.key)
        return {"success": True}

    async def evaluate_answer(self, ref, answer):
        self.evaluated.append((ref, answer))
        return {"success": True}


class FakeVideoAgent:
    def __init__(self):
        self.sent = []

    async def send_daily_video(self, ref):
        self.sent.append(ref)
        return {"success": True, "video_id": 1, "title": "Intro"}

    async def get_user_video_progress(self, ref):
        return {
            "success": True,
            "progress": {
                "total_videos": 10, "watched_videos": 3, "completion_rate": 30.0,
                "total_questions_answered": 6, "average_score": 7.5,
            },
        }


class FakeRagAgent:
    def __init__(self):
        self.queries = []
        self.listed = []

    async def query_documents(self, query, ref):
        self.queries.append((query, ref))
        return {"success": True}

    async def list_available_documents(self, ref):
        self.listed.append(ref)
        return {"success": True}


class FakeOrchestrator:
    def __init__(self, router):
        from agents.orchestrator import AgentType

        self.router = router
        self.routed = []
        self.agents = {
            AgentType.VIDEO: FakeVideoAgent(),
            AgentType.QUESTION: FakeQuestionAgent(),
            AgentType.RAG: FakeRagAgent(),
        }

    async def get_agent(self, agent_type):
        return self.agents.get(agent_type)

    def has_active_quiz(self, ref):
        from agents.orchestrator import AgentType

        return self.agents[AgentType.QUESTION].has_active_quiz(ref)

    async def process_message(self, ref, text):
        self.routed.append((ref, text))
        return {"success": True, "agent": "video"}


@pytest.fixture
def orchestrator(router):
    return FakeOrchestrator(router)


@pytest.fixture
def dispatcher(orchestrator):
    return CommandDispatcher(orchestrator)


@pytest.fixture
def wa_ref():
    return UserRef(Platform.WHATSAPP, "15551234567")


@pytest.fixture
def tg_ref():
    return UserRef(Platform.TELEGRAM, "6437411483")


class TestParseCommand:
    def test_slash_command_with_args(self):
        parsed = parse_command("/ask what is the leave policy", allow_bare=True)
        assert parsed.command == "ask"
        assert parsed.args == "what is the leave policy"
        assert parsed.is_explicit is True

    def test_telegram_group_suffix_is_stripped(self):
        assert parse_command("/video@MyLearningBot", allow_bare=False).command == "lesson"

    def test_bare_word_accepted_when_allowed(self):
        """WhatsApp has no slash-command menu, so bare keywords must work."""
        assert parse_command("lesson", allow_bare=True).command == "lesson"

    def test_old_video_wording_still_routes(self):
        """Learners and old links still say "video"; it must keep working."""
        for word in ("video", "watch", "listen", "read"):
            assert parse_command(word, allow_bare=True).command == "lesson"

    def test_bare_word_ignored_when_not_allowed(self):
        assert parse_command("video", allow_bare=False).command is None

    def test_greetings_alias_to_start(self):
        assert parse_command("hi", allow_bare=True).command == "start"

    def test_menu_is_its_own_command(self):
        """`menu` reopens the button menu; it is no longer an alias for help."""
        assert parse_command("menu", allow_bare=True).command == "menu"

    def test_case_insensitive(self):
        assert parse_command("/VIDEO", allow_bare=True).command == "lesson"

    def test_free_text_is_not_a_command(self):
        parsed = parse_command("photosynthesis converts light into energy", allow_bare=True)
        assert parsed.command is None
        assert parsed.args == "photosynthesis converts light into energy"

    def test_empty_text(self):
        assert parse_command("   ", allow_bare=True).command is None


@pytest.mark.asyncio
class TestCommandParity:
    """Both platforms must behave identically for the same command."""

    @pytest.mark.parametrize("text", ["/video", "video"])
    async def test_video_command_on_whatsapp(self, dispatcher, orchestrator, wa_ref, text):
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, text, Profile(first_name="Alice"))
        assert orchestrator.agents[AgentType.VIDEO].sent == [wa_ref]

    async def test_video_command_on_telegram(self, dispatcher, orchestrator, tg_ref):
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(tg_ref, "/video", Profile(first_name="Bob"))
        assert orchestrator.agents[AgentType.VIDEO].sent == [tg_ref]

    async def test_replies_go_to_the_right_platform(self, dispatcher, wa_ref,
                                                    fake_whatsapp_client, fake_telegram_client):
        await dispatcher.handle_text(wa_ref, "/help")
        assert len(fake_whatsapp_client.messages) == 1
        assert fake_telegram_client.messages == []

    async def test_quiz_command_starts_a_session(self, dispatcher, orchestrator, wa_ref):
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "/quiz")
        assert orchestrator.agents[AgentType.QUESTION].started == [wa_ref]

    async def test_ask_without_a_question_prompts_for_one(self, dispatcher, orchestrator,
                                                          wa_ref, fake_whatsapp_client):
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "/ask")
        assert orchestrator.agents[AgentType.RAG].queries == []
        assert "*Ask a question*" in fake_whatsapp_client.messages[-1][1]
        # The learner is now expected to type the question as a plain message.
        assert wa_ref.key in dispatcher._awaiting_question

    async def test_ask_forwards_the_query(self, dispatcher, orchestrator, wa_ref):
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "/ask What is the leave policy?")
        assert orchestrator.agents[AgentType.RAG].queries[0][0] == "What is the leave policy?"

    async def test_docs_lists_documents(self, dispatcher, orchestrator, wa_ref):
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "/docs")
        assert orchestrator.agents[AgentType.RAG].listed == [wa_ref]

    async def test_progress_reports_stats(self, dispatcher, wa_ref, fake_whatsapp_client):
        await dispatcher.handle_text(wa_ref, "/progress")
        body = fake_whatsapp_client.messages[-1][1]
        assert "3 of 10 done" in body
        assert "7.5/10" in body

    async def test_unknown_command_shows_the_menu(self, dispatcher, wa_ref, fake_whatsapp_client):
        """A wrong guess should offer the options, not just say no."""
        await dispatcher.handle_text(wa_ref, "/teleport")
        _, _, ids = fake_whatsapp_client.menus[-1]
        assert "lesson" in ids and "quiz" in ids


@pytest.mark.asyncio
class TestQuizFlow:
    async def test_free_text_during_a_quiz_is_graded(self, dispatcher, orchestrator, wa_ref):
        from agents.orchestrator import AgentType

        question_agent = orchestrator.agents[AgentType.QUESTION]
        question_agent.active.add(wa_ref.key)

        await dispatcher.handle_text(wa_ref, "Because photosynthesis needs light")

        assert question_agent.evaluated == [(wa_ref, "Because photosynthesis needs light")]

    async def test_bare_keyword_during_a_quiz_is_treated_as_an_answer(self, dispatcher,
                                                                     orchestrator, wa_ref):
        """A learner answering 'video' mid-quiz must not trigger the video command."""
        from agents.orchestrator import AgentType

        question_agent = orchestrator.agents[AgentType.QUESTION]
        question_agent.active.add(wa_ref.key)

        await dispatcher.handle_text(wa_ref, "video")

        assert question_agent.evaluated == [(wa_ref, "video")]
        assert orchestrator.agents[AgentType.VIDEO].sent == []

    async def test_slash_command_during_a_quiz_still_runs(self, dispatcher, orchestrator, wa_ref):
        """Telegram parity: explicit commands bypass the quiz answer handler."""
        from agents.orchestrator import AgentType

        orchestrator.agents[AgentType.QUESTION].active.add(wa_ref.key)

        await dispatcher.handle_text(wa_ref, "/video")

        assert orchestrator.agents[AgentType.VIDEO].sent == [wa_ref]
        assert orchestrator.agents[AgentType.QUESTION].evaluated == []

    async def test_quizzes_are_isolated_per_platform(self, dispatcher, orchestrator,
                                                     wa_ref, tg_ref):
        """Same numeric id on two platforms must not share quiz state."""
        from agents.orchestrator import AgentType

        question_agent = orchestrator.agents[AgentType.QUESTION]
        question_agent.active.add(wa_ref.key)

        assert question_agent.has_active_quiz(wa_ref) is True
        assert question_agent.has_active_quiz(UserRef(Platform.TELEGRAM, "15551234567")) is False


@pytest.mark.asyncio
class TestFreeform:
    async def test_free_text_is_routed_and_hinted(self, dispatcher, orchestrator,
                                                  wa_ref, fake_whatsapp_client):
        await dispatcher.handle_text(wa_ref, "tell me about onboarding stuff")
        assert len(orchestrator.routed) == 1
        _, _, ids = fake_whatsapp_client.menus[-1]
        assert "lesson" in ids

    async def test_unsupported_media_gets_a_reply(self, dispatcher, wa_ref, fake_whatsapp_client):
        await dispatcher.handle_unsupported(wa_ref, "image")
        to, prompt, ids = fake_whatsapp_client.menus[-1]
        assert "read text right now" in prompt
        assert "lesson" in ids

    async def test_handler_errors_are_contained(self, dispatcher, orchestrator,
                                                wa_ref, fake_whatsapp_client):
        from agents.orchestrator import AgentType

        async def explode(ref):
            raise RuntimeError("agent exploded")

        orchestrator.agents[AgentType.VIDEO].send_daily_video = explode

        result = await dispatcher.handle_text(wa_ref, "/video")

        assert result["handled_as"] == "error"
        assert "Something went wrong" in fake_whatsapp_client.messages[-1][1]


@pytest.mark.asyncio
class TestInteractiveMenus:
    """The menu is how a WhatsApp learner discovers what the bot can do."""

    async def test_start_sends_the_main_menu(self, dispatcher, wa_ref, fake_whatsapp_client,
                                             monkeypatch):
        # Registration is the only DB touch on this path; stub it so the test
        # covers what the learner actually sees.
        registered = []
        monkeypatch.setattr(
            "dispatcher.get_or_create_user_from_ref",
            lambda ref, **kw: registered.append((ref, kw)),
        )

        await dispatcher.handle_text(wa_ref, "hi", Profile(first_name="Mithran"))

        assert len(registered) == 1   # cmd_start registers; register_inbound is the webhook's job
        assert "*Welcome to MicroLearning, Mithran*" in fake_whatsapp_client.messages[-1][1]
        _, _, ids = fake_whatsapp_client.menus[-1]
        assert ids == ["lesson", "quiz", "ask", "progress", "docs", "help"]

    async def test_finishing_a_lesson_offers_the_quiz(self, dispatcher, wa_ref,
                                                      fake_whatsapp_client):
        await dispatcher.handle_text(wa_ref, "lesson")

        _, prompt, ids = fake_whatsapp_client.menus[-1]
        assert prompt == "Finished with that one?"
        # Three or fewer, so WhatsApp renders these as real buttons.
        assert ids == ["quiz", "lesson", "menu"]

    async def test_button_tap_is_a_command_not_a_quiz_answer(self, dispatcher, orchestrator,
                                                             wa_ref):
        """
        The regression this guards: mid-quiz, bare words are answers. A learner
        tapping "Take a quiz" would otherwise have "quiz" graded as their answer.
        """
        from agents.orchestrator import AgentType

        question_agent = orchestrator.agents[AgentType.QUESTION]
        question_agent.active.add(wa_ref.key)

        await dispatcher.handle_text(wa_ref, "video", from_button=True)

        assert question_agent.evaluated == []
        assert orchestrator.agents[AgentType.VIDEO].sent == [wa_ref]

    async def test_typed_word_mid_quiz_is_still_an_answer(self, dispatcher, orchestrator,
                                                          wa_ref):
        from agents.orchestrator import AgentType

        question_agent = orchestrator.agents[AgentType.QUESTION]
        question_agent.active.add(wa_ref.key)

        await dispatcher.handle_text(wa_ref, "video")

        assert question_agent.evaluated == [(wa_ref, "video")]

    async def test_unrecognised_button_id_falls_back_to_the_menu(self, dispatcher, wa_ref,
                                                                 fake_whatsapp_client):
        await dispatcher.handle_text(wa_ref, "some-stale-id", from_button=True)

        _, _, ids = fake_whatsapp_client.menus[-1]
        assert "lesson" in ids

    async def test_tapping_ask_then_typing_reaches_the_rag_agent(self, dispatcher,
                                                                 orchestrator, wa_ref):
        """Two-step flow: the button carries no text, so the next message is the question."""
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "ask", from_button=True)
        assert orchestrator.agents[AgentType.RAG].queries == []

        await dispatcher.handle_text(wa_ref, "what is the leave policy")

        queries = orchestrator.agents[AgentType.RAG].queries
        assert queries == [("what is the leave policy", wa_ref)]
        # The pending state is one-shot.
        assert wa_ref.key not in dispatcher._awaiting_question

    async def test_pending_question_is_cleared_by_another_command(self, dispatcher,
                                                                  orchestrator, wa_ref):
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "ask", from_button=True)
        await dispatcher.handle_text(wa_ref, "progress", from_button=True)
        await dispatcher.handle_text(wa_ref, "just chatting")

        # The stray message must not be treated as the forgotten question.
        assert orchestrator.agents[AgentType.RAG].queries == []
        assert len(orchestrator.routed) == 1

    async def test_telegram_gets_the_same_menu(self, dispatcher, tg_ref, fake_telegram_client):
        """Parity: the channels must not drift."""
        await dispatcher.handle_text(tg_ref, "/menu")

        _, _, ids = fake_telegram_client.menus[-1]
        assert ids == ["lesson", "quiz", "ask", "progress", "docs", "help"]
