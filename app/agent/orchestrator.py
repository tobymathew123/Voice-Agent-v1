"""LangChain-based agent orchestrator for conversation management."""

import logging
from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.config import settings
from app.agent.prompts import BFSIPrompts, NOTIFICATION_PROMPT, MARKETING_PROMPT
from app.agent.tools import get_tools_for_persona

logger = logging.getLogger(__name__)


class VoiceAgentOrchestrator:
    """LangChain-based orchestrator for voice agent conversations.
    
    Manages conversation state, agent reasoning, and tool calling.
    Stateless across calls - memory is per-session only.
    """
    
    def __init__(
        self,
        persona: str = "bank",
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 150  # Keep responses concise for voice
    ):
        """Initialize agent orchestrator.
        
        Args:
            persona: Agent persona (bank, insurance, financial_services)
            model: OpenAI model name (defaults to config)
            temperature: Response randomness (0-1)
            max_tokens: Maximum response length
        """
        self.persona = persona
        self.model = model or settings.OPENAI_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        # Get tools for persona
        self.tools = get_tools_for_persona(persona)
        
        # Create prompt template
        self.prompt = BFSIPrompts.create_chat_prompt(persona)
        
        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Session-based memory storage
        self._memories: Dict[str, ConversationBufferMemory] = {}
        
        logger.info(f"Agent orchestrator initialized: persona={persona}, model={self.model}")
    
    def _get_or_create_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create conversation memory for session.
        
        Args:
            session_id: Call session ID
            
        Returns:
            ConversationBufferMemory for this session
        """
        if session_id not in self._memories:
            self._memories[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="output"
            )
            logger.info(f"Created new memory for session: {session_id}")
        
        return self._memories[session_id]
    
    def clear_session_memory(self, session_id: str):
        """Clear memory for a session.
        
        Args:
            session_id: Call session ID
        """
        if session_id in self._memories:
            del self._memories[session_id]
            logger.info(f"Cleared memory for session: {session_id}")
    
    async def process_user_input(
        self,
        user_input: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process user input and generate response.
        
        Args:
            user_input: User's speech input
            session_id: Call session ID
            context: Additional context (call type, metadata, etc.)
            
        Returns:
            Agent's response text
        """
        try:
            logger.info(f"Processing input for session {session_id}: '{user_input}'")
            
            # Get memory for this session
            memory = self._get_or_create_memory(session_id)
            
            # Create agent executor with memory
            agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=memory,
                verbose=True,
                max_iterations=3,  # Limit iterations for voice
                handle_parsing_errors=True,
            )
            
            # Execute agent
            result = await agent_executor.ainvoke({"input": user_input})
            
            response = result.get("output", "I apologize, I didn't understand that. Could you please rephrase?")
            
            # Post-process response for voice
            response = self._post_process_response(response)
            
            logger.info(f"Agent response: '{response}'")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing user input: {str(e)}", exc_info=True)
            return "I apologize, I'm having trouble processing that. Could you please try again?"
    
    def _post_process_response(self, response: str) -> str:
        """Post-process response for voice delivery.
        
        Args:
            response: Raw agent response
            
        Returns:
            Processed response suitable for voice
        """
        # Remove markdown formatting
        response = response.replace("**", "").replace("*", "")
        
        # Remove bullet points
        response = response.replace("- ", "").replace("• ", "")
        
        # Limit length (split into sentences, take first 2-3)
        sentences = response.split(". ")
        if len(sentences) > 3:
            response = ". ".join(sentences[:3]) + "."
        
        # Remove URLs (not useful in voice)
        # Simple removal - can be enhanced
        if "http" in response.lower():
            response = response.split("http")[0].strip()
        
        return response.strip()
    
    async def generate_notification_response(
        self,
        message: str,
        session_id: str
    ) -> str:
        """Generate response for notification delivery.
        
        Args:
            message: Notification message to deliver
            session_id: Call session ID
            
        Returns:
            Agent response
        """
        try:
            prompt = NOTIFICATION_PROMPT.format(message=message)
            
            response = await self.llm.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content="Please deliver the notification.")
            ])
            
            return self._post_process_response(response.content)
            
        except Exception as e:
            logger.error(f"Error generating notification response: {str(e)}")
            return message  # Fallback to raw message
    
    async def generate_marketing_response(
        self,
        campaign_name: str,
        objective: str,
        segment: str,
        user_input: Optional[str] = None,
        session_id: str = None
    ) -> str:
        """Generate response for marketing call.
        
        Args:
            campaign_name: Marketing campaign name
            objective: Campaign objective
            segment: Target segment
            user_input: User's response (if any)
            session_id: Call session ID
            
        Returns:
            Agent response
        """
        try:
            prompt = MARKETING_PROMPT.format(
                campaign_name=campaign_name,
                objective=objective,
                segment=segment
            )
            
            messages = [SystemMessage(content=prompt)]
            
            if user_input:
                messages.append(HumanMessage(content=user_input))
            else:
                messages.append(HumanMessage(content="Start the marketing call."))
            
            response = await self.llm.ainvoke(messages)
            
            return self._post_process_response(response.content)
            
        except Exception as e:
            logger.error(f"Error generating marketing response: {str(e)}")
            return f"Hello! I'm calling about {campaign_name}. Would you be interested in learning more?"


# Global agent instances for different personas
# These are stateless - memory is per-session
_agents: Dict[str, VoiceAgentOrchestrator] = {}


def get_agent(persona: str = "bank") -> VoiceAgentOrchestrator:
    """Get or create agent for persona.
    
    Args:
        persona: Agent persona
        
    Returns:
        VoiceAgentOrchestrator instance
    """
    if persona not in _agents:
        _agents[persona] = VoiceAgentOrchestrator(persona=persona)
    
    return _agents[persona]


# Convenience function for telephony handlers
async def process_call_input(
    user_input: str,
    session_id: str,
    persona: str = "bank",
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Process user input in a call.
    
    Args:
        user_input: User's speech
        session_id: Call session ID
        persona: Agent persona
        context: Additional context
        
    Returns:
        Agent response
    """
    agent = get_agent(persona)
    return await agent.process_user_input(user_input, session_id, context)
