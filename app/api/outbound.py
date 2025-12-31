"""Outbound call API endpoints."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from typing import Optional
import logging

from app.storage.models import (
    OutboundCallRequest,
    CallType,
    CallDirection,
    CallStatus,
    CampaignMetadata,
    NotificationMetadata
)
from app.telephony.vobiz_client import vobiz_client
from app.telephony.session_manager import session_manager
from app.telephony.xml_builder import VobizXMLResponse, create_error_response
from app.agent.orchestrator import get_agent
from app.storage.data_capture import MarketingCallData, extract_user_interest, UserInterest
from app.storage.csv_storage import csv_storage

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/notification")
async def initiate_notification_call(
    to_number: str,
    notification_type: str,
    message: str,
    priority: str = "normal",
    reference_id: Optional[str] = None,
    from_number: Optional[str] = None,
    webhook_base_url: str = "https://your-domain.com"  # TODO: Get from config
):
    """Initiate a notification call.
    
    Args:
        to_number: Recipient phone number
        notification_type: Type of notification (otp, alert, reminder, etc.)
        message: Notification message to deliver
        priority: Priority level (low, normal, high, urgent)
        reference_id: Optional reference ID for tracking
        from_number: Optional caller ID
        webhook_base_url: Base URL for webhooks
        
    Returns:
        Call initiation response with call_sid
    """
    try:
        # Create notification metadata
        notification_metadata = NotificationMetadata(
            notification_type=notification_type,
            priority=priority,
            message=message,
            reference_id=reference_id
        )
        
        # Create outbound call request
        request = OutboundCallRequest(
            to_number=to_number,
            from_number=from_number,
            call_type=CallType.NOTIFICATION,
            notification_metadata=notification_metadata
        )
        
        # Initiate call via Vobiz API
        result = await vobiz_client.initiate_call(request, webhook_base_url)
        
        # Create session for tracking (try multiple field names for call_sid)
        call_sid = (
            result.get("CallSid") or 
            result.get("call_sid") or 
            result.get("CallUUID") or 
            result.get("call_uuid") or
            result.get("request_uuid") or
            result.get("RequestUUID")
        )
        
        logger.info(f"Creating session with call_sid: {call_sid}, Vobiz response: {result}")
        
        if call_sid:
            session = session_manager.create_session(
                call_id=call_sid,
                from_number=from_number or "system",
                to_number=to_number,
                direction=CallDirection.OUTBOUND,
                call_type=CallType.NOTIFICATION,
                metadata={
                    "notification_type": notification_type,
                    "priority": priority,
                    "message": message,
                    "reference_id": reference_id,
                    "vobiz_response": result
                }
            )
            session.notification_metadata = notification_metadata.model_dump()
            
            logger.info(f"Notification call initiated: {call_sid}")
        
        return {
            "status": "initiated",
            "call_sid": call_sid,
            "to_number": to_number,
            "call_type": "notification",
            "notification_type": notification_type
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate notification call: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")


@router.post("/marketing")
async def initiate_marketing_call(
    to_number: str,
    campaign_id: str,
    campaign_name: str,
    segment: Optional[str] = None,
    objective: Optional[str] = None,
    from_number: Optional[str] = None,
    webhook_base_url: str = "https://your-domain.com"  # TODO: Get from config
):
    """Initiate a marketing call.
    
    Args:
        to_number: Recipient phone number
        campaign_id: Unique campaign identifier
        campaign_name: Campaign name
        segment: Customer segment
        objective: Campaign objective
        from_number: Optional caller ID
        webhook_base_url: Base URL for webhooks
        
    Returns:
        Call initiation response with call_sid
    """
    try:
        # Create campaign metadata
        campaign_metadata = CampaignMetadata(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            segment=segment,
            objective=objective
        )
        
        # Create outbound call request
        request = OutboundCallRequest(
            to_number=to_number,
            from_number=from_number,
            call_type=CallType.MARKETING,
            campaign_metadata=campaign_metadata
        )
        
        # Initiate call via Vobiz API
        result = await vobiz_client.initiate_call(request, webhook_base_url)
        
        # Create session for tracking
        call_sid = result.get("CallSid") or result.get("call_sid")
        if call_sid:
            session = session_manager.create_session(
                call_id=call_sid,
                from_number=from_number or "system",
                to_number=to_number,
                direction=CallDirection.OUTBOUND,
                call_type=CallType.MARKETING,
                metadata={
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "segment": segment,
                    "objective": objective,
                    "vobiz_response": result
                }
            )
            session.campaign_metadata = campaign_metadata.model_dump()
            
            logger.info(f"Marketing call initiated: {call_sid} for campaign {campaign_id}")
        
        return {
            "status": "initiated",
            "call_sid": call_sid,
            "to_number": to_number,
            "call_type": "marketing",
            "campaign_id": campaign_id,
            "campaign_name": campaign_name
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate marketing call: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")


@router.post("/notification/handle")
async def handle_notification_call(request: Request):
    """Handle notification call webhook from Vobiz.ai.
    
    This webhook is called when the notification call is answered.
    Returns XML to play the notification message.
    """
    try:
        # Parse form data
        form_data = await request.form()
        
        # Log all form data to debug
        logger.info(f"Notification webhook received. Form data: {dict(form_data)}")
        
        # Try multiple field names for call_sid (Vobiz might use different naming)
        call_sid = (
            form_data.get("CallSid") or 
            form_data.get("call_sid") or 
            form_data.get("CallUUID") or
            form_data.get("call_uuid")
        )
        
        logger.info(f"Notification call answered: {call_sid}")
        
        # Get session
        session = session_manager.get_session(call_sid)
        
        # Fallback: If session not found, use default test message
        if not session or not session.notification_metadata:
            logger.warning(f"Session or notification metadata not found: {call_sid}. Using fallback message.")
            
            # Use default test message as fallback
            default_message = """Hello. This is an automated test call from the AI voice agent platform.
This call is being made to verify outbound calling functionality.
No action is required from you.
Thank you."""
            
            # Build simple XML response with default message
            xml_response = (
                VobizXMLResponse()
                .say(default_message)
                .pause(1)
                .say("Goodbye.")
                .hangup()
                .build()
            )
            
            return Response(content=xml_response, media_type="application/xml")
        
        # Update status
        session_manager.update_status(call_sid, CallStatus.IN_PROGRESS)
        
        # Get notification message
        message = session.notification_metadata.get("message", "This is a notification.")
        
        # Generate AI response for notification delivery
        agent = get_agent(persona="bank")
        ai_response = await agent.generate_notification_response(message, call_sid)
        
        # Build XML response to deliver notification
        xml_response = (
            VobizXMLResponse()
            .say(ai_response)
            .pause(1)
            .say("Thank you. Goodbye.")
            .hangup()
            .build()
        )
        
        return Response(content=xml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling notification call: {str(e)}", exc_info=True)
        error_xml = create_error_response()
        return Response(content=error_xml, media_type="application/xml")


@router.post("/marketing/handle")
async def handle_marketing_call(request: Request):
    """Handle marketing call webhook from Vobiz.ai.
    
    This webhook is called when the marketing call is answered.
    Returns XML to start the marketing conversation.
    """
    try:
        # Parse form data
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        
        logger.info(f"Marketing call answered: {call_sid}")
        
        # Get session
        session = session_manager.get_session(call_sid)
        if not session or not session.campaign_metadata:
            logger.warning(f"Session or campaign metadata not found: {call_sid}")
            error_xml = create_error_response("Session not found.")
            return Response(content=error_xml, media_type="application/xml")
        
        # Update status
        session_manager.update_status(call_sid, CallStatus.IN_PROGRESS)
        
        # Get campaign info
        campaign_name = session.campaign_metadata.get("campaign_name", "our service")
        objective = session.campaign_metadata.get("objective", "product promotion")
        segment = session.campaign_metadata.get("segment", "valued customers")
        
        # Generate AI marketing message
        agent = get_agent(persona="bank")
        ai_message = await agent.generate_marketing_response(
            campaign_name=campaign_name,
            objective=objective,
            segment=segment,
            session_id=call_sid
        )
        
        # Build XML response with marketing message and data capture
        # TODO: This will be replaced with AI agent integration
        callback_url = f"/telephony/outbound/marketing/gather/{call_sid}"
        
        xml_response = (
            VobizXMLResponse()
            .say(ai_message)
            .gather_with_prompt(
                prompt_text="Are you interested in learning more? Please say yes or no.",
                action=callback_url,
                timeout=5,
                input_type="speech"
            )
            .say("Thank you for your time. Goodbye.")
            .hangup()
            .build()
        )
        
        return Response(content=xml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling marketing call: {str(e)}", exc_info=True)
        error_xml = create_error_response()
        return Response(content=error_xml, media_type="application/xml")


@router.post("/marketing/gather/{call_id}")
async def handle_marketing_gather(call_id: str, request: Request):
    """Handle gathered response from marketing call.
    
    This captures the user's response to marketing questions.
    """
    try:
        form_data = await request.form()
        speech_result = form_data.get("SpeechResult")
        
        logger.info(f"Marketing call response for {call_id}: {speech_result}")
        
        # Get session
        session = session_manager.get_session(call_id)
        if not session:
            error_xml = create_error_response("Session not found.")
            return Response(content=error_xml, media_type="application/xml")
        
        # Process response with AI agent
        agent = get_agent(persona="bank")
        campaign_name = session.campaign_metadata.get("campaign_name", "our service")
        objective = session.campaign_metadata.get("objective", "product promotion")
        segment = session.campaign_metadata.get("segment", "valued customers")
        
        ai_response = await agent.generate_marketing_response(
            campaign_name=campaign_name,
            objective=objective,
            segment=segment,
            user_input=speech_result or "No response",
            session_id=call_id
        )
        
        # Store response in conversation history
        session_manager.add_conversation_turn(
            call_id=call_id,
            role="user",
            content=speech_result or "No response",
            metadata={"input_type": "speech", "marketing_response": True}
        )
        
        session_manager.add_conversation_turn(
            call_id=call_id,
            role="assistant",
            content=ai_response,
            metadata={"marketing_response": True}
        )
        
        # Extract and save structured data
        user_interest = extract_user_interest(speech_result or "")
        
        # Calculate call duration
        call_duration = None
        if session.created_at and session.ended_at:
            call_duration = int((session.ended_at - session.created_at).total_seconds())
        
        # Create marketing call data record
        marketing_data = MarketingCallData(
            call_id=call_id,
            campaign_id=session.campaign_metadata.get("campaign_id", "unknown"),
            campaign_name=session.campaign_metadata.get("campaign_name", "unknown"),
            user_interest=user_interest,
            language="en-IN",  # TODO: Get from session
            call_started_at=session.created_at,
            call_ended_at=session.ended_at,
            call_duration_seconds=call_duration,
            segment=session.campaign_metadata.get("segment"),
            objective=session.campaign_metadata.get("objective"),
            call_status="completed",
            notes=f"User response: {speech_result[:100] if speech_result else 'No response'}"
        )
        
        # Save to CSV
        csv_storage.save_marketing_call(marketing_data)
        logger.info(f"Marketing data captured: {call_id}, interest={user_interest}")
        
        # Build response
        xml_response = (
            VobizXMLResponse()
            .say(ai_response)
            .say("Goodbye.")
            .hangup()
            .build()
        )
        
        return Response(content=xml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling marketing gather: {str(e)}", exc_info=True)
        error_xml = create_error_response()
        return Response(content=error_xml, media_type="application/xml")
