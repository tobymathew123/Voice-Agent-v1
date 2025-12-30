"""Call metrics tracking models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class CallMetrics(BaseModel):
    """Comprehensive call metrics for tracking and analytics.
    
    Designed to power admin dashboard with call statistics,
    cost tracking, and performance metrics.
    """
    
    # Call identification
    call_id: str = Field(..., description="Unique call identifier")
    vobiz_call_sid: Optional[str] = Field(None, description="Vobiz CallSid")
    
    # Call classification
    direction: str = Field(..., description="inbound or outbound")
    call_type: str = Field(..., description="general, notification, marketing, customer_service")
    
    # Phone numbers (anonymized for privacy)
    from_number_hash: Optional[str] = Field(None, description="Hashed caller number")
    to_number_hash: Optional[str] = Field(None, description="Hashed recipient number")
    
    # Timing metrics
    call_started_at: datetime = Field(..., description="Call initiation time")
    call_answered_at: Optional[datetime] = Field(None, description="Call answer time")
    call_ended_at: Optional[datetime] = Field(None, description="Call end time")
    
    # Duration metrics (in seconds)
    ring_duration: Optional[int] = Field(None, description="Time to answer")
    talk_duration: Optional[int] = Field(None, description="Conversation duration")
    total_duration: Optional[int] = Field(None, description="Total call duration")
    
    # Call outcome
    call_status: str = Field(..., description="completed, failed, no_answer, busy")
    disconnect_reason: Optional[str] = Field(None, description="Reason for call end")
    
    # Cost tracking (from Vobiz CDR)
    call_cost: Optional[float] = Field(None, description="Call cost in currency")
    currency: str = Field(default="INR", description="Currency code")
    
    # Quality metrics
    audio_quality: Optional[str] = Field(None, description="good, fair, poor")
    transcript_available: bool = Field(default=False, description="Whether transcript exists")
    
    # Campaign/context (for outbound)
    campaign_id: Optional[str] = Field(None, description="Campaign identifier")
    agent_persona: Optional[str] = Field(None, description="bank, insurance, financial_services")
    
    # Performance metrics
    user_turns: int = Field(default=0, description="Number of user responses")
    agent_turns: int = Field(default=0, description="Number of agent responses")
    
    # Metadata
    language: str = Field(default="en-IN", description="Language used")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        use_enum_values = True


class DailyMetricsSummary(BaseModel):
    """Daily aggregated metrics for dashboard."""
    
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    
    # Call volume
    total_calls: int = 0
    inbound_calls: int = 0
    outbound_calls: int = 0
    
    # Call types
    marketing_calls: int = 0
    notification_calls: int = 0
    customer_service_calls: int = 0
    
    # Outcomes
    completed_calls: int = 0
    failed_calls: int = 0
    no_answer_calls: int = 0
    
    # Duration metrics
    avg_talk_duration: Optional[float] = None
    total_talk_duration: int = 0
    
    # Cost metrics
    total_cost: float = 0.0
    avg_cost_per_call: Optional[float] = None
    
    # Quality
    avg_user_turns: Optional[float] = None
    transcript_coverage: Optional[float] = None  # % of calls with transcripts


def calculate_call_metrics(session_data: dict) -> CallMetrics:
    """Calculate metrics from call session data.
    
    Args:
        session_data: Dictionary with call session information
        
    Returns:
        CallMetrics instance
    """
    # Calculate durations
    ring_duration = None
    talk_duration = None
    total_duration = None
    
    started_at = session_data.get('created_at')
    answered_at = session_data.get('answered_at')
    ended_at = session_data.get('ended_at')
    
    if started_at and answered_at:
        ring_duration = int((answered_at - started_at).total_seconds())
    
    if answered_at and ended_at:
        talk_duration = int((ended_at - answered_at).total_seconds())
    
    if started_at and ended_at:
        total_duration = int((ended_at - started_at).total_seconds())
    
    # Count conversation turns
    conversation_history = session_data.get('conversation_history', [])
    user_turns = len([t for t in conversation_history if t.get('role') == 'user'])
    agent_turns = len([t for t in conversation_history if t.get('role') == 'assistant'])
    
    # Create metrics
    return CallMetrics(
        call_id=session_data.get('call_id'),
        vobiz_call_sid=session_data.get('call_id'),  # Same for now
        direction=session_data.get('direction', 'inbound'),
        call_type=session_data.get('call_type', 'general'),
        call_started_at=started_at,
        call_answered_at=answered_at,
        call_ended_at=ended_at,
        ring_duration=ring_duration,
        talk_duration=talk_duration,
        total_duration=total_duration,
        call_status=session_data.get('status', 'completed'),
        campaign_id=session_data.get('metadata', {}).get('campaign_id'),
        user_turns=user_turns,
        agent_turns=agent_turns,
        language=session_data.get('language', 'en-IN'),
        transcript_available=len(conversation_history) > 0
    )


def hash_phone_number(phone_number: str) -> str:
    """Hash phone number for privacy.
    
    Args:
        phone_number: Phone number to hash
        
    Returns:
        Hashed phone number (last 4 digits visible)
    """
    import hashlib
    
    if not phone_number:
        return ""
    
    # Keep last 4 digits, hash the rest
    if len(phone_number) > 4:
        visible = phone_number[-4:]
        hashed = hashlib.md5(phone_number[:-4].encode()).hexdigest()[:8]
        return f"***{visible} ({hashed})"
    
    return phone_number
