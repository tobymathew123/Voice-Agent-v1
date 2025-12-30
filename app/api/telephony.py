"""Telephony webhook handlers for Vobiz.ai."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import Response
from typing import Optional
import logging

from app.storage.models import VobizCallEvent, CallDirection, CallStatus, CallType
from app.telephony.session_manager import session_manager
from app.telephony.xml_builder import (
    create_welcome_response,
    create_error_response,
    create_goodbye_response,
    VobizXMLResponse
)
from app.speech.processor import SpeechProcessor, generate_telephony_response
from app.agent.orchestrator import process_call_input, get_agent
from app.storage.metrics import calculate_call_metrics
from app.storage.metrics_storage import metrics_storage

router = APIRouter()
logger = logging.getLogger(__name__)

# TODO: Get from config or environment
BASE_URL = "https://your-domain.com"  # Replace with actual public URL


@router.post("/incoming")
async def handle_incoming_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: Optional[str] = Form(None),
    Direction: Optional[str] = Form(None),
    AccountSid: Optional[str] = Form(None),
    ApiVersion: Optional[str] = Form(None)
):
    """Handle incoming call webhook from Vobiz.ai.
    
    This is the initial webhook when a call comes in.
    Returns XML to control the call flow.
    """
    try:
        # Parse incoming event
        event = VobizCallEvent(
            CallSid=CallSid,
            From=From,
            To=To,
            CallStatus=CallStatus,
            Direction=Direction,
            AccountSid=AccountSid,
            ApiVersion=ApiVersion
        )
        
        logger.info(f"Incoming call: {event.CallSid} from {event.From} to {event.To}")
        
        # Create call session
        session = session_manager.create_session(
            call_id=event.CallSid,
            from_number=event.From,
            to_number=event.To,
            direction=CallDirection.INBOUND,
            call_type=CallType.GENERAL,
            metadata={
                "account_sid": event.AccountSid,
                "api_version": event.ApiVersion,
                "initial_status": event.CallStatus
            }
        )
        
        # Update status to in-progress
        session_manager.update_status(event.CallSid, CallStatus.IN_PROGRESS)
        
        logger.info(f"Session created: {session.call_id}")
        
        # Generate welcome message using Deepgram TTS
        welcome_text = "Welcome to our service. How may I help you today?"
        audio_path = await generate_telephony_response(welcome_text, language="en-IN")
        
        # Build callback URL for gathering speech
        callback_url = f"/telephony/gather/{event.CallSid}"
        
        # Build XML response with TTS audio
        if audio_path:
            # Convert local path to public URL
            audio_url = SpeechProcessor.get_audio_url_for_playback(audio_path, BASE_URL)
            
            xml_response = (
                VobizXMLResponse()
                .play(audio_url)
                .gather(
                    action=callback_url,
                    method="POST",
                    timeout=5,
                    input_type="speech"
                )
                .say("I didn't catch that. Please try again.")
                .redirect(callback_url)
                .build()
            )
        else:
            # Fallback to XML Say if TTS fails
            xml_response = create_welcome_response(callback_url)
        
        return Response(content=xml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {str(e)}", exc_info=True)
        error_xml = create_error_response()
        return Response(content=error_xml, media_type="application/xml")


@router.post("/gather/{call_id}")
async def handle_gather_response(
    call_id: str,
    SpeechResult: Optional[str] = Form(None),
    Digits: Optional[str] = Form(None),
    CallSid: Optional[str] = Form(None)
):
    """Handle gathered input (speech or DTMF) from caller.
    
    This webhook receives the user's speech or keypad input.
    """
    try:
        logger.info(f"Gather response for call {call_id}: speech={SpeechResult}, digits={Digits}")
        
        # Get session
        session = session_manager.get_session(call_id)
        if not session:
            logger.warning(f"Session not found: {call_id}")
            error_xml = create_error_response("Session not found.")
            return Response(content=error_xml, media_type="application/xml")
        
        # Process speech input
        if SpeechResult:
            # Add user input to conversation history
            session_manager.add_conversation_turn(
                call_id=call_id,
                role="user",
                content=SpeechResult,
                metadata={"input_type": "speech"}
            )
            
            logger.info(f"User said: {SpeechResult}")
            
            # Process with AI agent
            response_text = await process_call_input(
                user_input=SpeechResult,
                session_id=call_id,
                persona="bank",  # TODO: Get from session metadata
                context={
                    "call_type": session.call_type,
                    "direction": session.direction
                }
            )
            
            # Add assistant response to history
            session_manager.add_conversation_turn(
                call_id=call_id,
                role="assistant",
                content=response_text
            )
            
            # Generate TTS for response
            audio_path = await generate_telephony_response(response_text, language="en-IN")
            
            # Build response with next gather
            callback_url = f"/telephony/gather/{call_id}"
            
            if audio_path:
                audio_url = SpeechProcessor.get_audio_url_for_playback(audio_path, BASE_URL)
                
                # Generate follow-up question audio
                followup_text = "Is there anything else I can help you with?"
                followup_audio = await generate_telephony_response(followup_text, language="en-IN")
                followup_url = SpeechProcessor.get_audio_url_for_playback(followup_audio, BASE_URL) if followup_audio else None
                
                xml_response = (
                    VobizXMLResponse()
                    .play(audio_url)
                    .gather(
                        action=callback_url,
                        method="POST",
                        timeout=5,
                        input_type="speech"
                    )
                )
                
                if followup_url:
                    xml_response.play(followup_url)
                else:
                    xml_response.say(followup_text)
            else:
                # Fallback to XML Say
                xml_response = (
                    VobizXMLResponse()
                    .say(response_text)
                    .gather_with_prompt(
                        prompt_text="Is there anything else I can help you with?",
                        action=callback_url,
                        timeout=5,
                        input_type="speech"
                    )
                .say("Thank you for calling. Goodbye.")
                .hangup()
                .build()
            )
            
            return Response(content=xml_response, media_type="application/xml")
        
        # Process DTMF input
        elif Digits:
            session_manager.add_conversation_turn(
                call_id=call_id,
                role="user",
                content=Digits,
                metadata={"input_type": "dtmf"}
            )
            
            logger.info(f"User pressed: {Digits}")
            
            # Handle DTMF menu options
            response_text = f"You pressed {Digits}."
            xml_response = (
                VobizXMLResponse()
                .say(response_text)
                .say("Goodbye.")
                .hangup()
                .build()
            )
            
            return Response(content=xml_response, media_type="application/xml")
        
        # No input received
        else:
            logger.info(f"No input received for call {call_id}")
            xml_response = create_goodbye_response("I didn't receive any input. Goodbye.")
            return Response(content=xml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling gather response: {str(e)}", exc_info=True)
        error_xml = create_error_response()
        return Response(content=error_xml, media_type="application/xml")


@router.post("/events")
async def handle_call_events(
    CallSid: str = Form(...),
    CallStatus: Optional[str] = Form(None),
    CallDuration: Optional[str] = Form(None),
    RecordingUrl: Optional[str] = Form(None),
    RecordingDuration: Optional[str] = Form(None)
):
    """Handle call events (status updates, recordings, etc.) from Vobiz.ai.
    
    This webhook receives asynchronous events about call state changes.
    """
    try:
        logger.info(f"Call event: {CallSid} status={CallStatus} duration={CallDuration}")
        
        session = session_manager.get_session(CallSid)
        
        # Map Vobiz status to our status enum
        status_mapping = {
            "initiated": CallStatus.INITIATED,
            "ringing": CallStatus.RINGING,
            "in-progress": CallStatus.IN_PROGRESS,
            "completed": CallStatus.COMPLETED,
            "failed": CallStatus.FAILED,
            "busy": CallStatus.BUSY,
            "no-answer": CallStatus.NO_ANSWER
        }
        
        if CallStatus and CallStatus.lower() in status_mapping:
            new_status = status_mapping[CallStatus.lower()]
            
            if session:
                session_manager.update_status(CallSid, new_status)
                logger.info(f"Updated session {CallSid} to status {new_status}")
            
            # If call ended, clean up session
            if new_status in [CallStatus.COMPLETED, CallStatus.FAILED, CallStatus.NO_ANSWER, CallStatus.BUSY]:
                if session:
                    ended_session = session_manager.end_session(CallSid)
                    logger.info(f"Call ended: {CallSid}, duration: {CallDuration}s")
                    
                    # TODO: Persist call record to database
                    # TODO: Save transcript and metadata
        
        # Handle recording URL if provided
        if RecordingUrl and session:
            session.metadata["recording_url"] = RecordingUrl
            session.metadata["recording_duration"] = RecordingDuration
            logger.info(f"Recording available: {RecordingUrl}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error handling call event: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/outgoing")
async def handle_outgoing_call(request: Request):
    """Handle outgoing call webhook from Vobiz.ai."""
    # TODO: Implement outgoing call handling
    logger.info("Outgoing call handler - not yet implemented")
    return Response(content=create_error_response("Outgoing calls not yet supported."), media_type="application/xml")


@router.post("/notification")
async def handle_notification_call(request: Request):
    """Handle notification call webhook from Vobiz.ai."""
    # TODO: Implement notification call handling
    logger.info("Notification call handler - not yet implemented")
    return Response(content=create_error_response("Notification calls not yet supported."), media_type="application/xml")


@router.post("/marketing")
async def handle_marketing_call(request: Request):
    """Handle marketing call webhook from Vobiz.ai."""
    # TODO: Implement marketing call handling
    logger.info("Marketing call handler - not yet implemented")
    return Response(content=create_error_response("Marketing calls not yet supported."), media_type="application/xml")


@router.get("/session/{call_id}")
async def get_session_info(call_id: str):
    """Get current session information (for debugging/monitoring).
    
    Args:
        call_id: Call identifier
        
    Returns:
        Session data if found
    """
    session = session_manager.get_session(call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.get("/sessions")
async def list_active_sessions():
    """List all active sessions (for debugging/monitoring).
    
    Returns:
        Dictionary of active sessions
    """
    sessions = session_manager.get_active_sessions()
    return {
        "count": len(sessions),
        "sessions": sessions
    }
