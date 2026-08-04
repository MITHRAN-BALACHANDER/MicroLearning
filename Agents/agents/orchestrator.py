"""
Agent Orchestrator - Manages all agents dynamically using Agno principles

Platform-agnostic: agents receive a MessagingRouter, so the same orchestration
serves Telegram and WhatsApp learners at the same time.
"""
from typing import Any, Dict
from datetime import datetime
from enum import Enum

from loguru import logger

from agents.video_agent import VideoAgent
from agents.question_agent import QuestionAgent
from agents.rag_agent import RAGAgent
from agents.video_upload_agent import VideoUploadAgent
from agents.video_delivery_agent import VideoDeliveryAgent
from messaging.base import UserRef


class AgentType(Enum):
    """Types of agents in the system"""
    VIDEO = "video"
    QUESTION = "question"
    RAG = "rag"
    UPLOAD = "upload"
    DELIVERY = "delivery"
    ORCHESTRATOR = "orchestrator"


class AgentOrchestrator:
    """
    Dynamic agent orchestrator following Agno (AgentOS) principles:
    - Agents operate independently
    - Dynamic routing based on context
    - Shared state management
    - Scalable architecture
    """

    def __init__(self, router):
        """
        Args:
            router: MessagingRouter covering every enabled platform

        Agents are constructed on first use, not here. Building the RAG agent
        pulls in sentence-transformers and torch, which costs over two minutes
        on a cold start - long enough that Meta's webhook verification would
        time out before the HTTP server ever bound its port.
        """
        self.router = router
        self.name = "AgentOrchestrator"

        # Share one upload/delivery pair so media caches and stats stay global
        self._agents: Dict[AgentType, Any] = {}
        self._factories = {
            AgentType.UPLOAD: lambda: VideoUploadAgent(router),
            AgentType.DELIVERY: lambda: VideoDeliveryAgent(router),
            AgentType.VIDEO: lambda: VideoAgent(
                router,
                self.get_agent_sync(AgentType.UPLOAD),
                self.get_agent_sync(AgentType.DELIVERY),
            ),
            AgentType.QUESTION: lambda: QuestionAgent(router),
            AgentType.RAG: lambda: RAGAgent(router),
        }

        # Track user contexts for dynamic routing, keyed by UserRef.key
        self.user_contexts: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"Initialized {self.name} with {len(self._factories)} lazily-built agents "
            f"over {[p.value for p in router.platforms]}"
        )

    @property
    def agents(self) -> Dict[AgentType, Any]:
        """Agents built so far. Does not trigger construction."""
        return self._agents

    def get_agent_sync(self, agent_type: AgentType):
        """Get an agent, building it on first use."""
        if agent_type not in self._agents:
            factory = self._factories.get(agent_type)
            if factory is None:
                return None
            logger.info(f"Building {agent_type.value} agent on first use...")
            self._agents[agent_type] = factory()
        return self._agents[agent_type]

    def has_active_quiz(self, ref: UserRef) -> bool:
        """
        Whether this learner is mid-quiz.

        If the question agent has never been built nobody can be in a quiz, so
        this answers without forcing an expensive construction.
        """
        question_agent = self._agents.get(AgentType.QUESTION)
        if question_agent is None:
            return False
        return question_agent.has_active_quiz(ref)

    def warm_up(self, *agent_types) -> None:
        """Pre-build agents (e.g. in the background after the server binds)."""
        for agent_type in (agent_types or self._factories.keys()):
            try:
                self.get_agent_sync(agent_type)
            except Exception:
                logger.exception(f"Could not warm up the {agent_type.value} agent")

    def route_message(self, ref: UserRef, message: str, context: Dict = None) -> AgentType:
        """
        Dynamically route a message to the appropriate agent based on context

        Args:
            ref: UserRef identifying the learner and platform
            message: User's message
            context: Additional context

        Returns:
            AgentType to handle the message
        """
        message_lower = (message or "").lower()

        # A learner mid-quiz always goes to the question agent
        if self.has_active_quiz(ref):
            return AgentType.QUESTION

        if any(keyword in message_lower for keyword in ['video', 'watch', 'next video', 'daily']):
            return AgentType.VIDEO

        elif any(keyword in message_lower for keyword in ['quiz', 'question', 'test', 'answer']):
            return AgentType.QUESTION

        elif any(keyword in message_lower for keyword in ['ask', 'manual', 'sop', 'policy', 'document', 'how to']):
            return AgentType.RAG

        # Default to context-based routing
        user_context = self.user_contexts.get(ref.key, {})
        return user_context.get('last_agent', AgentType.VIDEO)

    async def process_message(self, ref: UserRef, message: str) -> Dict[str, Any]:
        """
        Process a message by routing it to the appropriate agent

        Args:
            ref: UserRef identifying the learner and platform
            message: User's message

        Returns:
            Dict with processing result
        """
        try:
            agent_type = self.route_message(ref, message)

            self.user_contexts[ref.key] = {
                'last_agent': agent_type,
                'last_message': message,
                'platform': ref.platform.value,
                'timestamp': datetime.utcnow(),
            }

            logger.info(
                f"Routing message from {ref} ({ref.platform.value}) to {agent_type.value} agent"
            )

            return {
                "success": True,
                "agent": agent_type.value,
                "message": "Message routed successfully"
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_agent(self, agent_type: AgentType):
        """Get a specific agent, building it on first use"""
        return self.get_agent_sync(agent_type)

    def get_all_agents_status(self) -> Dict[str, Any]:
        """
        Get status of all agents.

        Reports agents that have not been built yet as "not_built" rather than
        constructing them, so /health stays fast and side-effect free.
        """
        status = {}
        for agent_type in self._factories:
            agent = self._agents.get(agent_type)
            status[agent_type.value] = (
                agent.get_agent_state() if agent is not None
                else {"status": "not_built"}
            )
        status["messaging"] = self.router.get_state()
        return status

    async def broadcast_to_agents(self, message: str, data: Dict = None):
        """Broadcast a system-wide event to all agents"""
        logger.info(f"Broadcasting message: {message}")
        pass

    def cleanup_inactive_contexts(self, max_age_hours: int = 24) -> int:
        """Drop routing contexts that have gone stale"""
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        stale = [
            key for key, ctx in self.user_contexts.items()
            if ctx.get('timestamp') and ctx['timestamp'].timestamp() < cutoff
        ]
        for key in stale:
            del self.user_contexts[key]
        if stale:
            logger.info(f"Cleaned up {len(stale)} inactive user contexts")
        return len(stale)

    async def close(self):
        """Release messaging resources"""
        await self.router.close()
