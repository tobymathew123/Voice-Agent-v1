"""Data models for call logs and metrics."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CallDirection(str, Enum):
    """Call direction types."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallStatus(str, Enum):
    """Call status types."""
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"


class CallType(str, Enum):
    """Call type categories."""
    CUSTOMER_SERVICE = "customer_service"
    NOTIFICATION = "notification"
    MARKETING = "marketing"
    GENERAL = "general"


class CallSession(BaseModel):
    """Active call session state."""
    
    call_id: str = Field(..., description="Unique call identifier from Vobiz")
    direction: CallDirection
    call_type: CallType = CallType.GENERAL
    status: CallStatus = CallStatus.INITIATED
    
    # Caller information
    from_number: str = Field(..., description="Caller phone number")
    to_number: str = Field(..., description="Recipient phone number")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Session data
    conversation_history: list[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Audio processing state
    audio_stream_active: bool = False
    current_transcript: str = ""
    
    # Outbound call specific fields
    campaign_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Campaign metadata for marketing calls")
    notification_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Notification metadata")
    
    class Config:
        use_enum_values = True


class CampaignMetadata(BaseModel):
    """Marketing campaign metadata."""
    
    campaign_id: str = Field(..., description="Unique campaign identifier")
    campaign_name: str = Field(..., description="Campaign name")
    segment: Optional[str] = Field(None, description="Customer segment")
    objective: Optional[str] = Field(None, description="Campaign objective")
    
    # Data capture fields (for later implementation)
    expected_responses: Optional[list[str]] = Field(default=None, description="Expected response types")
    capture_schema: Optional[Dict[str, Any]] = Field(default=None, description="Data capture schema")


class NotificationMetadata(BaseModel):
    """Notification call metadata."""
    
    notification_type: str = Field(..., description="Type of notification (otp, alert, reminder, etc.)")
    priority: str = Field(default="normal", description="Priority level (low, normal, high, urgent)")
    message: str = Field(..., description="Notification message")
    reference_id: Optional[str] = Field(None, description="Reference ID for tracking")


class OutboundCallRequest(BaseModel):
    """Request model for initiating outbound calls."""
    
    to_number: str = Field(..., description="Recipient phone number")
    from_number: Optional[str] = Field(None, description="Caller ID (if not using default)")
    call_type: CallType
    
    # Type-specific metadata
    campaign_metadata: Optional[CampaignMetadata] = None
    notification_metadata: Optional[NotificationMetadata] = None
    
    # Additional options
    webhook_url: Optional[str] = Field(None, description="Custom webhook URL for this call")
    status_callback_url: Optional[str] = Field(None, description="Status callback URL")
    timeout: int = Field(default=60, description="Call timeout in seconds")
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CallRecord(BaseModel):
    """Persistent call record for storage."""
    
    call_id: str
    direction: CallDirection
    call_type: CallType
    status: CallStatus
    
    from_number: str
    to_number: str
    
    created_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class VobizCallEvent(BaseModel):
    """Incoming webhook event from Vobiz.ai."""
    
    CallSid: str = Field(..., description="Vobiz call identifier")
    From: str = Field(..., description="Caller number")
    To: str = Field(..., description="Recipient number")
    CallStatus: Optional[str] = None
    Direction: Optional[str] = None
    
    # Additional Vobiz fields
    AccountSid: Optional[str] = None
    ApiVersion: Optional[str] = None
    
    # Optional fields for different event types
    RecordingUrl: Optional[str] = None
    RecordingDuration: Optional[str] = None
    Digits: Optional[str] = None  # DTMF input
    SpeechResult: Optional[str] = None  # Speech recognition result
