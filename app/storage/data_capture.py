"""Data capture models and storage for marketing calls."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class UserInterest(str, Enum):
    """User interest level for marketing calls."""
    YES = "yes"
    NO = "no"
    MAYBE = "maybe"
    UNSURE = "unsure"
    NO_RESPONSE = "no_response"


class MarketingCallData(BaseModel):
    """Structured data captured from marketing call.
    
    NOTE: No personal information (names, phone numbers, addresses) is stored.
    Only aggregated response data for campaign analytics.
    """
    
    # Call metadata
    call_id: str = Field(..., description="Call session ID")
    campaign_id: str = Field(..., description="Campaign identifier")
    campaign_name: str = Field(..., description="Campaign name")
    
    # Response data
    user_interest: UserInterest = Field(..., description="User interest level")
    language: str = Field(default="en-IN", description="Language used in call")
    
    # Timestamps
    call_started_at: datetime = Field(..., description="Call start time")
    call_ended_at: Optional[datetime] = Field(None, description="Call end time")
    
    # Call metrics
    call_duration_seconds: Optional[int] = Field(None, description="Call duration")
    response_time_seconds: Optional[int] = Field(None, description="Time to first response")
    
    # Campaign context
    segment: Optional[str] = Field(None, description="Target segment")
    objective: Optional[str] = Field(None, description="Campaign objective")
    
    # Additional metadata (non-personal)
    call_status: str = Field(..., description="Call completion status")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        use_enum_values = True


class NotificationCallData(BaseModel):
    """Structured data for notification calls."""
    
    call_id: str
    notification_type: str  # otp, alert, reminder, etc.
    priority: str
    
    delivered: bool = Field(default=False, description="Whether notification was delivered")
    acknowledged: bool = Field(default=False, description="Whether user acknowledged")
    
    call_started_at: datetime
    call_ended_at: Optional[datetime] = None
    call_duration_seconds: Optional[int] = None
    
    language: str = "en-IN"
    call_status: str
    
    class Config:
        use_enum_values = True


def extract_user_interest(user_response: str) -> UserInterest:
    """Extract user interest from natural language response.
    
    Args:
        user_response: User's spoken response
        
    Returns:
        UserInterest enum value
    """
    if not user_response or not user_response.strip():
        return UserInterest.NO_RESPONSE
    
    response_lower = user_response.lower().strip()
    
    # Yes indicators
    yes_keywords = ["yes", "yeah", "sure", "okay", "ok", "interested", "definitely", "absolutely"]
    if any(keyword in response_lower for keyword in yes_keywords):
        return UserInterest.YES
    
    # No indicators
    no_keywords = ["no", "nope", "not interested", "don't", "never", "not now"]
    if any(keyword in response_lower for keyword in no_keywords):
        return UserInterest.NO
    
    # Maybe indicators
    maybe_keywords = ["maybe", "perhaps", "might", "think about", "consider", "later"]
    if any(keyword in response_lower for keyword in maybe_keywords):
        return UserInterest.MAYBE
    
    # Default to unsure
    return UserInterest.UNSURE
