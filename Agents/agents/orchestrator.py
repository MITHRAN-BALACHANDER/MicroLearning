"""
Agent Orchestrator - Manages all agents dynamically using Agno principles
"""
from typing import Dict, Any, Optional
from loguru import logger
from enum import Enum

from agents.video_agent import VideoAgent
from agents.question_agent import QuestionAgent
from agents.rag_agent import RAGAgent


class AgentType(Enum):
    """Types of agents in the system"""
    VIDEO = "video"
    QUESTION = "question"
    RAG = "rag"
    ORCHESTRATOR = "orchestrator"


class AgentOrchestrator:
    """
    Dynamic agent orchestrator following Agno (AgentOS) principles:
    - Agents operate independently
    - Dynamic routing based on context
    - Shared state management
    - Scalable architecture
    """
    
    def __init__(self, telegram_bot):
        self.bot = telegram_bot
        self.name = "AgentOrchestrator"
        
        # Initialize all agents
        self.agents = {
            AgentType.VIDEO: VideoAgent(telegram_bot),
            AgentType.QUESTION: QuestionAgent(telegram_bot),
            AgentType.RAG: RAGAgent(telegram_bot)
        }
        
        # Track user contexts for dynamic routing
        self.user_contexts = {}
        
        logger.info(f"Initialized {self.name} with {len(self.agents)} agents")
    
    def route_message(self, telegram_id: str, message: str, context: Dict = None) -> AgentType:
        """
        Dynamically route message to appropriate agent based on context
        
        Args:
            telegram_id: User's Telegram ID
            message: User's message
            context: Additional context
            
        Returns:
            AgentType to handle the message
        """
        message_lower = message.lower()
        
        # Check if user is in active quiz
        if telegram_id in self.agents[AgentType.QUESTION].active_quizzes:
            return AgentType.QUESTION
        
        # Route based on keywords and commands
        if any(keyword in message_lower for keyword in ['video', 'watch', 'next video', 'daily']):
            return AgentType.VIDEO
        
        elif any(keyword in message_lower for keyword in ['quiz', 'question', 'test', 'answer']):
            return AgentType.QUESTION
        
        elif any(keyword in message_lower for keyword in ['ask', 'manual', 'sop', 'policy', 'document', 'how to']):
            return AgentType.RAG
        
        # Default to context-based routing
        user_context = self.user_contexts.get(telegram_id, {})
        last_agent = user_context.get('last_agent', AgentType.VIDEO)
        
        return last_agent
    
    async def process_message(self, telegram_id: str, message: str) -> Dict[str, Any]:
        """
        Process a message by routing to appropriate agent
        
        Args:
            telegram_id: User's Telegram ID
            message: User's message
            
        Returns:
            Dict with processing result
        """
        try:
            # Determine which agent should handle this
            agent_type = self.route_message(telegram_id, message)
            
            # Update user context
            self.user_contexts[telegram_id] = {
                'last_agent': agent_type,
                'last_message': message,
                'timestamp': None
            }
            
            logger.info(f"Routing message from {telegram_id} to {agent_type.value} agent")
            
            return {
                "success": True,
                "agent": agent_type.value,
                "message": "Message routed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_agent(self, agent_type: AgentType):
        """Get a specific agent"""
        return self.agents.get(agent_type)
    
    def get_all_agents_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            agent_type.value: agent.get_agent_state()
            for agent_type, agent in self.agents.items()
        }
    
    async def broadcast_to_agents(self, message: str, data: Dict = None):
        """
        Broadcast a message to all agents (for system-wide events)
        
        Args:
            message: Message type
            data: Additional data
        """
        logger.info(f"Broadcasting message: {message}")
        # Implement inter-agent communication if needed
        pass
    
    def cleanup_inactive_contexts(self, max_age_hours: int = 24):
        """Clean up old user contexts"""
        # Implement cleanup logic
        pass
