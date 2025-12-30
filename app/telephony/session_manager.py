"""Call session manager for tracking active calls."""

from typing import Dict, Optional
from datetime import datetime

from app.storage.models import CallSession, CallDirection, CallStatus, CallType


class SessionManager:
    """In-memory session manager for active calls."""
    
    def __init__(self):
        """Initialize session storage."""
        self._sessions: Dict[str, CallSession] = {}
    
    def create_session(
        self,
        call_id: str,
        from_number: str,
        to_number: str,
        direction: CallDirection,
        call_type: CallType = CallType.GENERAL,
        metadata: Optional[Dict] = None
    ) -> CallSession:
        """Create a new call session.
        
        Args:
            call_id: Unique call identifier
            from_number: Caller phone number
            to_number: Recipient phone number
            direction: Call direction (inbound/outbound)
            call_type: Type of call
            metadata: Additional metadata
            
        Returns:
            Created CallSession
        """
        session = CallSession(
            call_id=call_id,
            from_number=from_number,
            to_number=to_number,
            direction=direction,
            call_type=call_type,
            status=CallStatus.INITIATED,
            metadata=metadata or {}
        )
        
        self._sessions[call_id] = session
        return session
    
    def get_session(self, call_id: str) -> Optional[CallSession]:
        """Retrieve a call session.
        
        Args:
            call_id: Call identifier
            
        Returns:
            CallSession if found, None otherwise
        """
        return self._sessions.get(call_id)
    
    def update_status(self, call_id: str, status: CallStatus) -> Optional[CallSession]:
        """Update call status.
        
        Args:
            call_id: Call identifier
            status: New status
            
        Returns:
            Updated CallSession if found, None otherwise
        """
        session = self._sessions.get(call_id)
        if session:
            session.status = status
            
            # Update timestamps based on status
            if status == CallStatus.IN_PROGRESS and not session.answered_at:
                session.answered_at = datetime.utcnow()
            elif status in [CallStatus.COMPLETED, CallStatus.FAILED, CallStatus.NO_ANSWER, CallStatus.BUSY]:
                session.ended_at = datetime.utcnow()
        
        return session
    
    def add_conversation_turn(
        self,
        call_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Optional[CallSession]:
        """Add a conversation turn to the session.
        
        Args:
            call_id: Call identifier
            role: Speaker role (user/assistant/system)
            content: Message content
            metadata: Additional turn metadata
            
        Returns:
            Updated CallSession if found, None otherwise
        """
        session = self._sessions.get(call_id)
        if session:
            turn = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            session.conversation_history.append(turn)
        
        return session
    
    def set_audio_stream_active(self, call_id: str, active: bool) -> Optional[CallSession]:
        """Set audio stream state.
        
        Args:
            call_id: Call identifier
            active: Whether audio stream is active
            
        Returns:
            Updated CallSession if found, None otherwise
        """
        session = self._sessions.get(call_id)
        if session:
            session.audio_stream_active = active
        
        return session
    
    def update_transcript(self, call_id: str, transcript: str) -> Optional[CallSession]:
        """Update current transcript.
        
        Args:
            call_id: Call identifier
            transcript: Transcript text
            
        Returns:
            Updated CallSession if found, None otherwise
        """
        session = self._sessions.get(call_id)
        if session:
            session.current_transcript = transcript
        
        return session
    
    def end_session(self, call_id: str) -> Optional[CallSession]:
        """End and remove a call session.
        
        Args:
            call_id: Call identifier
            
        Returns:
            Removed CallSession if found, None otherwise
        """
        session = self._sessions.pop(call_id, None)
        if session and not session.ended_at:
            session.ended_at = datetime.utcnow()
            session.status = CallStatus.COMPLETED
        
        return session
    
    def get_active_sessions(self) -> Dict[str, CallSession]:
        """Get all active sessions.
        
        Returns:
            Dictionary of active sessions
        """
        return self._sessions.copy()
    
    def clear_all(self):
        """Clear all sessions (for testing/cleanup)."""
        self._sessions.clear()


# Global session manager instance
session_manager = SessionManager()
