"""Unit tests for the agent orchestrator routing logic."""
import pytest
from unittest.mock import MagicMock, patch

from messaging.base import Platform, UserRef


def make_orchestrator(router, build_all=True):
    """Build an orchestrator with all agents mocked out."""
    patches = [
        patch("agents.orchestrator.VideoAgent"),
        patch("agents.orchestrator.QuestionAgent"),
        patch("agents.orchestrator.RAGAgent"),
        patch("agents.orchestrator.VideoUploadAgent"),
        patch("agents.orchestrator.VideoDeliveryAgent"),
    ]
    started = [p.start() for p in patches]
    try:
        from agents.orchestrator import AgentOrchestrator, AgentType

        # No learner is mid-quiz unless a test says otherwise
        started[1].return_value.has_active_quiz = MagicMock(return_value=False)
        orchestrator = AgentOrchestrator(router)
        if build_all:
            # Agents are lazy; most tests want them present
            orchestrator.warm_up()
        return orchestrator, AgentType
    finally:
        for p in patches:
            p.stop()


@pytest.fixture
def orchestrator(router):
    return make_orchestrator(router)


@pytest.fixture
def ref():
    return UserRef(Platform.TELEGRAM, "123456789")


class TestIntentRouting:
    """Test that the orchestrator routes messages to the correct agent."""

    def test_video_keyword_routes_to_video_agent(self, orchestrator, ref):
        orch, AgentType = orchestrator
        assert orch.route_message(ref, "video") == AgentType.VIDEO

    def test_quiz_keyword_routes_to_question_agent(self, orchestrator, ref):
        orch, AgentType = orchestrator
        assert orch.route_message(ref, "quiz") == AgentType.QUESTION

    def test_ask_keyword_routes_to_rag_agent(self, orchestrator, ref):
        orch, AgentType = orchestrator
        assert orch.route_message(ref, "ask what is the policy") == AgentType.RAG

    def test_policy_keyword_routes_to_rag_agent(self, orchestrator, ref):
        orch, AgentType = orchestrator
        assert orch.route_message(ref, "what is the leave policy") == AgentType.RAG

    def test_unknown_message_falls_back_to_video(self, orchestrator, ref):
        orch, AgentType = orchestrator
        assert orch.route_message(ref, "hello there") == AgentType.VIDEO

    def test_active_quiz_session_routes_to_question_agent(self, orchestrator, ref):
        orch, AgentType = orchestrator
        orch.agents[AgentType.QUESTION].has_active_quiz = MagicMock(return_value=True)
        assert orch.route_message(ref, "some random answer") == AgentType.QUESTION

    def test_last_agent_is_remembered_per_user(self, orchestrator, ref):
        orch, AgentType = orchestrator
        orch.user_contexts[ref.key] = {"last_agent": AgentType.RAG}
        assert orch.route_message(ref, "hello there") == AgentType.RAG


class TestPlatformIsolation:
    def test_contexts_are_keyed_per_platform(self, orchestrator):
        """The same raw id on two platforms must keep separate routing state."""
        orch, AgentType = orchestrator
        telegram = UserRef(Platform.TELEGRAM, "15551234567")
        whatsapp = UserRef(Platform.WHATSAPP, "15551234567")

        orch.user_contexts[telegram.key] = {"last_agent": AgentType.RAG}

        assert orch.route_message(telegram, "hello") == AgentType.RAG
        assert orch.route_message(whatsapp, "hello") == AgentType.VIDEO


@pytest.mark.asyncio
class TestProcessMessage:
    async def test_records_platform_in_context(self, orchestrator):
        orch, _ = orchestrator
        ref = UserRef(Platform.WHATSAPP, "15551234567")

        result = await orch.process_message(ref, "show me a video")

        assert result["success"] is True
        assert orch.user_contexts[ref.key]["platform"] == "whatsapp"

    async def test_cleanup_drops_stale_contexts(self, orchestrator, ref):
        from datetime import datetime, timedelta

        orch, AgentType = orchestrator
        orch.user_contexts[ref.key] = {
            "last_agent": AgentType.VIDEO,
            "timestamp": datetime.utcnow() - timedelta(hours=48),
        }

        assert orch.cleanup_inactive_contexts(max_age_hours=24) == 1
        assert orch.user_contexts == {}
