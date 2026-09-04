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
    async def test_a_question_is_answered_not_menued(self, dispatcher, orchestrator,
                                                     wa_ref):
        """
        A learner who asks something gets an answer.

        This used to hand back the main menu, which reads as "I wasn't
        listening" when they had just said exactly what they wanted.
        """
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "tell me about onboarding stuff")

        assert orchestrator.agents[AgentType.RAG].queries == [
            ("tell me about onboarding stuff", wa_ref)
        ]

    async def test_tanglish_question_is_answered_not_menued(self, dispatcher,
                                                            orchestrator, wa_ref):
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "enaku evalo leave iruku oru masathula")

        assert orchestrator.agents[AgentType.RAG].queries == [
            ("enaku evalo leave iruku oru masathula", wa_ref)
        ]

    async def test_indian_script_question_is_answered_not_menued(self, dispatcher,
                                                                 orchestrator, wa_ref):
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "मुझे एक महीने में कितनी छुट्टी मिलेगी")

        assert orchestrator.agents[AgentType.RAG].queries == [
            ("मुझे एक महीने में कितनी छुट्टी मिलेगी", wa_ref)
        ]

    async def test_a_spoken_style_request_runs_the_command(self, dispatcher,
                                                           orchestrator, wa_ref):
        """Nobody says "lesson" - they say "send me the next video"."""
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "can you send me the next video please")

        assert orchestrator.agents[AgentType.VIDEO].sent == [wa_ref]

    async def test_longest_phrase_wins(self, dispatcher, orchestrator, wa_ref):
        """"next video" must beat the bare "video" inside it."""
        from agents.orchestrator import AgentType

        await dispatcher.handle_text(wa_ref, "give me a quiz")

        assert orchestrator.agents[AgentType.QUESTION].started == [wa_ref]
        assert orchestrator.agents[AgentType.VIDEO].sent == []

    async def test_genuinely_unrecognised_text_falls_back_to_the_menu(
        self, dispatcher, orchestrator, wa_ref, fake_whatsapp_client
    ):
        """The menu is the answer only when nothing else is."""
        from agents.orchestrator import AgentType

        result = await dispatcher.handle_text(wa_ref, "asdfgh zxcvb")

        assert result["handled_as"] == "unrecognised"
        assert orchestrator.agents[AgentType.RAG].queries == []
        assert orchestrator.agents[AgentType.VIDEO].sent == []
        _, prompt, ids = fake_whatsapp_client.menus[-1]
        assert "didn't catch" in prompt
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
        await dispatcher.handle_text(wa_ref, "asdfgh zxcvb")

        # The stray message must not be treated as the forgotten question.
        assert orchestrator.agents[AgentType.RAG].queries == []

    async def test_telegram_gets_the_same_menu(self, dispatcher, tg_ref, fake_telegram_client):
        """Parity: the channels must not drift."""
        await dispatcher.handle_text(tg_ref, "/menu")

        _, _, ids = fake_telegram_client.menus[-1]
        assert ids == ["lesson", "quiz", "ask", "progress", "docs", "help"]


class FakeTranscriber:
    """Stands in for the Whisper wrapper so tests never load a model."""

    def __init__(self, text="hello", error=None):
        from utils.transcription import Transcript

        self.transcript = Transcript(
            text=text, language="en", audio_seconds=3.0, elapsed_seconds=0.3,
            model="fake",
        )
        self.error = error
        self.calls = []

    async def transcribe(self, data, *, filename_hint="audio"):
        self.calls.append((data, filename_hint))
        if self.error:
            raise self.error
        return self.transcript


@pytest.fixture
def voice(monkeypatch):
    """Install a fake transcriber and hand it back so tests can retune it."""
    import dispatcher as dispatcher_module

    holder = {"transcriber": FakeTranscriber()}
    monkeypatch.setattr(
        dispatcher_module, "get_transcriber", lambda: holder["transcriber"]
    )
    return holder


class TestVoiceInput:
    """
    A voice note must do everything typing does.

    Anything less and voice becomes a second-class input that learners stop
    using the moment it fails them once.
    """

    async def test_spoken_command_runs_the_command(self, dispatcher, orchestrator,
                                                   voice, tg_ref):
        from agents.orchestrator import AgentType

        voice["transcriber"] = FakeTranscriber("Quiz.")

        await dispatcher.handle_audio(tg_ref, "file-id-1")

        # Whisper punctuates what it hears; "Quiz." is still the quiz command.
        assert orchestrator.agents[AgentType.QUESTION].started == [tg_ref]

    async def test_spoken_answer_is_graded(self, dispatcher, orchestrator, voice, tg_ref):
        from agents.orchestrator import AgentType

        question_agent = orchestrator.agents[AgentType.QUESTION]
        question_agent.active.add(tg_ref.key)
        voice["transcriber"] = FakeTranscriber(
            "The policy allows twenty days of paid leave."
        )

        await dispatcher.handle_audio(tg_ref, "file-id-2")

        assert question_agent.evaluated == [
            (tg_ref, "The policy allows twenty days of paid leave.")
        ]

    async def test_spoken_question_reaches_the_documents(self, dispatcher, orchestrator,
                                                        voice, wa_ref):
        from agents.orchestrator import AgentType

        # Tapping "Ask a question" then speaking the question.
        await dispatcher.handle_text(wa_ref, "ask", from_button=True)
        voice["transcriber"] = FakeTranscriber("what is the leave policy")

        await dispatcher.handle_audio(wa_ref, "media-id-1")

        assert orchestrator.agents[AgentType.RAG].queries == [
            ("what is the leave policy", wa_ref)
        ]

    async def test_transcript_is_read_back_before_it_is_acted_on(self, dispatcher, voice,
                                                                 tg_ref, fake_telegram_client):
        """Speech recognition mishears; the learner has to be able to see it."""
        voice["transcriber"] = FakeTranscriber("what is the leave policy")

        await dispatcher.handle_audio(tg_ref, "file-id-3")

        sent = [text for _, text in fake_telegram_client.messages]
        assert any("what is the leave policy" in text for text in sent)

    async def test_echo_can_be_switched_off(self, dispatcher, voice, tg_ref,
                                            monkeypatch, fake_telegram_client):
        """Off, the transcript is acted on but never quoted back."""
        from config import settings

        monkeypatch.setattr(settings, "VOICE_ECHO_TRANSCRIPT", False)
        voice["transcriber"] = FakeTranscriber("what is the leave policy")

        await dispatcher.handle_audio(tg_ref, "file-id-3b")

        sent = [text for _, text in fake_telegram_client.messages]
        assert not any("what is the leave policy" in text for text in sent)

    async def test_switching_the_echo_off_still_acts_on_the_transcript(
        self, dispatcher, orchestrator, voice, tg_ref, monkeypatch
    ):
        """Hiding the echo must not turn voice into a no-op."""
        from agents.orchestrator import AgentType
        from config import settings

        monkeypatch.setattr(settings, "VOICE_ECHO_TRANSCRIPT", False)
        voice["transcriber"] = FakeTranscriber("quiz")

        await dispatcher.handle_audio(tg_ref, "file-id-3c")

        assert orchestrator.agents[AgentType.QUESTION].started == [tg_ref]

    async def test_no_waiting_message_is_sent(self, dispatcher, voice, tg_ref,
                                              fake_telegram_client):
        """
        Transcription is sub-second on a GPU, so a "Listening..." placeholder
        was just an extra message in the thread.
        """
        voice["transcriber"] = FakeTranscriber("progress")

        await dispatcher.handle_audio(tg_ref, "file-id-3d")

        sent = [text for _, text in fake_telegram_client.messages]
        assert not any("Listening" in text for text in sent)

    async def test_media_is_fetched_from_the_learners_platform(self, dispatcher, voice,
                                                              wa_ref, fake_whatsapp_client):
        await dispatcher.handle_audio(wa_ref, "media-id-2")

        assert fake_whatsapp_client.downloads[0][0] == "media-id-2"
        assert voice["transcriber"].calls[0][0] == b"fake-audio-bytes"

    async def test_silence_asks_for_a_retry(self, dispatcher, orchestrator, voice,
                                            tg_ref, fake_telegram_client):
        voice["transcriber"] = FakeTranscriber("   ")

        result = await dispatcher.handle_audio(tg_ref, "file-id-4")

        assert result["handled_as"] == "voice_empty"
        assert orchestrator.routed == []
        assert any("couldn't make out" in text for _, text in fake_telegram_client.messages)

    async def test_long_recording_is_refused_before_downloading(self, dispatcher, voice,
                                                               tg_ref, fake_telegram_client):
        """The length is known from metadata, so a huge file costs nothing."""
        result = await dispatcher.handle_audio(tg_ref, "file-id-5", duration_seconds=99999)

        assert result["handled_as"] == "voice_too_long"
        assert fake_telegram_client.downloads == []
        assert voice["transcriber"].calls == []

    async def test_download_failure_degrades_to_a_prompt_for_text(self, dispatcher, voice,
                                                                  tg_ref, fake_telegram_client):
        from messaging.base import PermanentMessagingError

        fake_telegram_client.download_error = PermanentMessagingError("file_id expired")

        result = await dispatcher.handle_audio(tg_ref, "file-id-6")

        assert result["handled_as"] == "voice_failed"
        assert any("as text" in text for _, text in fake_telegram_client.messages)

    async def test_missing_model_does_not_look_like_the_learners_fault(self, dispatcher, voice,
                                                                      tg_ref, fake_telegram_client):
        from utils.transcription import TranscriptionUnavailable

        voice["transcriber"] = FakeTranscriber(
            error=TranscriptionUnavailable("faster-whisper is not installed")
        )

        result = await dispatcher.handle_audio(tg_ref, "file-id-7")

        assert result["handled_as"] == "voice_unavailable"
        # Still a way forward, and still a menu.
        assert fake_telegram_client.menus

    async def test_disabled_flag_turns_voice_off_without_touching_the_model(
        self, dispatcher, voice, tg_ref, monkeypatch, fake_telegram_client
    ):
        from config import settings

        monkeypatch.setattr(settings, "VOICE_INPUT_ENABLED", False)

        result = await dispatcher.handle_audio(tg_ref, "file-id-8")

        assert result["handled_as"] == "voice_disabled"
        assert fake_telegram_client.downloads == []

    async def test_both_channels_take_the_same_path(self, dispatcher, orchestrator,
                                                    voice, tg_ref, wa_ref):
        """Parity: a spoken command behaves identically on Telegram and WhatsApp."""
        from agents.orchestrator import AgentType

        voice["transcriber"] = FakeTranscriber("progress")

        tg_result = await dispatcher.handle_audio(tg_ref, "file-id-9")
        wa_result = await dispatcher.handle_audio(wa_ref, "media-id-3")

        assert tg_result["handled_as"] == wa_result["handled_as"] == "voice:progress"


class TestIntentResolution:
    """Unit-level checks on what maps to a command and what does not."""

    def test_bare_command_still_wins(self):
        from dispatcher import resolve_intent

        assert resolve_intent("quiz") == "quiz"
        assert resolve_intent("/progress") == "progress"

    def test_natural_phrasing_resolves(self):
        from dispatcher import resolve_intent

        assert resolve_intent("send me the next video") == "lesson"
        assert resolve_intent("Can I take the quiz now?") == "quiz"
        assert resolve_intent("how am i doing so far") == "progress"
        assert resolve_intent("what documents do you have") == "docs"

    def test_longest_phrase_wins_over_a_substring(self):
        from dispatcher import resolve_intent

        # "quiz me" (7) must beat "quiz" (4) - both point at quiz, but the
        # rule that picks between them is what keeps "next video" > "video".
        assert resolve_intent("please quiz me on that") == "quiz"
        assert resolve_intent("play the video") == "lesson"

    def test_noise_resolves_to_nothing(self):
        from dispatcher import resolve_intent

        assert resolve_intent("asdfgh zxcvb") is None
        assert resolve_intent("") is None
        assert resolve_intent("   ") is None

    def test_question_detection(self):
        from dispatcher import looks_like_a_question

        assert looks_like_a_question("what is the leave policy?") is True
        assert looks_like_a_question("How do I claim expenses") is True
        assert looks_like_a_question("tell me about the dress code") is True
        assert looks_like_a_question("asdfgh") is False


class TestSpokenCommandsInAnyLanguage:
    """
    A command spoken in Tamil must reach the same handler as the typed English.

    Whisper's translate pass is what makes that work without anyone keeping a
    keyword list per language.
    """

    async def test_non_english_command_routes_via_translation(
        self, dispatcher, orchestrator, voice, wa_ref
    ):
        from agents.orchestrator import AgentType
        from utils.transcription import Transcript

        native = FakeTranscriber("அடுத்த வீடியோ அனுப்பு")
        native.transcript.language = "ta"
        # The second pass, task="translate", renders it into English.
        native.translated = Transcript(
            text="Send the next video", language="en", model="fake"
        )

        async def transcribe(data, *, filename_hint="audio", task="transcribe"):
            native.calls.append((data, filename_hint, task))
            return native.translated if task == "translate" else native.transcript

        native.transcribe = transcribe
        voice["transcriber"] = native

        await dispatcher.handle_audio(wa_ref, "media-ta-1")

        assert orchestrator.agents[AgentType.VIDEO].sent == [wa_ref]
        assert [c[2] for c in native.calls] == ["transcribe", "translate"]

    async def test_english_audio_never_pays_for_a_translation_pass(
        self, dispatcher, voice, tg_ref
    ):
        """The extra inference only runs when it can change the outcome."""
        voice["transcriber"] = FakeTranscriber("send me the next video")

        await dispatcher.handle_audio(tg_ref, "file-en-1")

        assert len(voice["transcriber"].calls) == 1

    async def test_no_translation_when_the_native_text_already_resolves(
        self, dispatcher, voice, tg_ref
    ):
        native = FakeTranscriber("quiz")
        native.transcript.language = "ta"
        voice["transcriber"] = native

        await dispatcher.handle_audio(tg_ref, "file-ta-2")

        assert len(native.calls) == 1

    async def test_quiz_answers_are_never_translated(self, dispatcher, orchestrator,
                                                     voice, tg_ref):
        """
        Mid-quiz the learner's own words are the answer being graded.
        Translating them would change what gets scored.
        """
        from agents.orchestrator import AgentType

        question_agent = orchestrator.agents[AgentType.QUESTION]
        question_agent.active.add(tg_ref.key)

        native = FakeTranscriber("பதில் இது தான்")
        native.transcript.language = "ta"
        voice["transcriber"] = native

        await dispatcher.handle_audio(tg_ref, "file-ta-3")

        assert len(native.calls) == 1
        assert question_agent.evaluated == [(tg_ref, "பதில் இது தான்")]

    async def test_translation_can_be_switched_off(self, dispatcher, voice, tg_ref,
                                                   monkeypatch):
        from config import settings

        monkeypatch.setattr(settings, "VOICE_TRANSLATE_FOR_COMMANDS", False)
        native = FakeTranscriber("அடுத்த வீடியோ அனுப்பு")
        native.transcript.language = "ta"
        voice["transcriber"] = native

        await dispatcher.handle_audio(tg_ref, "file-ta-4")

        assert len(native.calls) == 1


class TestQuestionRetrievalLanguage:
    """
    The document index is embedded with an English-only model, so a question
    asked in another language has to be retrieved with its translation.
    """

    async def test_translated_reading_is_what_reaches_the_documents(
        self, dispatcher, orchestrator, voice, wa_ref
    ):
        from agents.orchestrator import AgentType
        from utils.transcription import Transcript

        native_text = "ஒரு மாசத்துல எத்தனை லீவு இருக்கு?"
        english_text = "How many days leave are there in a month?"

        fake = FakeTranscriber(native_text)
        fake.transcript.language = "ta"
        translated = Transcript(text=english_text, language="en", model="fake")

        async def transcribe(data, *, filename_hint="audio", task="transcribe"):
            fake.calls.append((data, filename_hint, task))
            return translated if task == "translate" else fake.transcript

        fake.transcribe = transcribe
        voice["transcriber"] = fake

        await dispatcher.handle_audio(wa_ref, "media-ta-q")

        assert orchestrator.agents[AgentType.RAG].queries == [(english_text, wa_ref)]

    async def test_question_form_survives_a_translation_that_drops_it(
        self, dispatcher, orchestrator, voice, wa_ref
    ):
        """
        Whisper's translation flattened "How many days leave are there?" into
        "I have a month's leave" - a statement. Detection must still see the
        question, because the original kept its "?".
        """
        from agents.orchestrator import AgentType
        from utils.transcription import Transcript

        fake = FakeTranscriber("எனக்கு எத்தனை லீவு இருக்கு?")
        fake.transcript.language = "ta"
        flattened = Transcript(text="I have a month's leave", language="en", model="fake")

        async def transcribe(data, *, filename_hint="audio", task="transcribe"):
            fake.calls.append((data, filename_hint, task))
            return flattened if task == "translate" else fake.transcript

        fake.transcribe = transcribe
        voice["transcriber"] = fake

        await dispatcher.handle_audio(wa_ref, "media-ta-q2")

        # Detected as a question from the original, retrieved with the English.
        assert orchestrator.agents[AgentType.RAG].queries == [
            ("I have a month's leave", wa_ref)
        ]

    async def test_english_question_is_unaffected(self, dispatcher, orchestrator,
                                                  voice, tg_ref):
        from agents.orchestrator import AgentType

        voice["transcriber"] = FakeTranscriber("what is the leave policy?")

        await dispatcher.handle_audio(tg_ref, "file-en-q")

        assert orchestrator.agents[AgentType.RAG].queries == [
            ("what is the leave policy?", tg_ref)
        ]
