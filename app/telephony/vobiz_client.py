"""Vobiz.ai API client for making outbound calls and managing telephony."""

import httpx
from typing import Optional, Dict, Any
from base64 import b64encode
import logging

from app.config import settings
from app.storage.models import OutboundCallRequest, CallType

logger = logging.getLogger(__name__)


class VobizClient:
    """Async HTTP client for Vobiz.ai REST API."""
    
    def __init__(self):
        """Initialize Vobiz client with authentication."""
        self.base_url = settings.VOBIZ_API_URL
        self.auth_id = settings.VOBIZ_AUTH_ID
        self.auth_token = settings.VOBIZ_AUTH_TOKEN
        
        # Create authorization header (Basic Auth)
        credentials = f"{self.auth_id}:{self.auth_token}"
        encoded_credentials = b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
    
    async def initiate_call(
        self,
        request: OutboundCallRequest,
        webhook_base_url: str
    ) -> Dict[str, Any]:
        """Initiate an outbound call via Vobiz.ai API.
        
        Args:
            request: Outbound call request details
            webhook_base_url: Base URL for webhooks (e.g., https://yourdomain.com)
            
        Returns:
            API response with call details
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        # Determine webhook URL based on call type
        if request.call_type == CallType.NOTIFICATION:
            webhook_path = f"/telephony/outbound/notification/handle"
        elif request.call_type == CallType.MARKETING:
            webhook_path = f"/telephony/outbound/marketing/handle"
        else:
            webhook_path = f"/telephony/outbound/handle"
        
        webhook_url = request.webhook_url or f"{webhook_base_url}{webhook_path}"
        status_callback_url = request.status_callback_url or f"{webhook_base_url}/telephony/events"
        
        # Build API request payload (Vobiz uses lowercase field names)
        payload = {
            "to": request.to_number,
            "from": request.from_number or settings.VOBIZ_FROM_NUMBER,  # Required by Vobiz
            "answer_url": webhook_url,  # Vobiz calls this 'answer_url' not 'url'
            "method": "POST",
            "status_callback": status_callback_url,
            "status_callback_method": "POST",
            "timeout": request.timeout
        }
        
        # Add custom parameters for metadata
        if request.campaign_metadata:
            payload["campaign_id"] = request.campaign_metadata.campaign_id
            payload["campaign_name"] = request.campaign_metadata.campaign_name
        
        if request.notification_metadata:
            payload["notification_type"] = request.notification_metadata.notification_type
            payload["priority"] = request.notification_metadata.priority
        
        # API endpoint
        endpoint = f"{self.base_url}/api/v1/Account/{self.auth_id}/Call/"
        
        logger.info(f"Initiating outbound call to {request.to_number} via {endpoint}")
        logger.debug(f"Request payload: {payload}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Call initiated successfully: {result.get('CallSid', 'N/A')}")
                return result
                
            except httpx.HTTPStatusError as e:
                # Log the error response body for debugging
                error_detail = e.response.text
                logger.error(f"Failed to initiate call: {str(e)}")
                logger.error(f"Vobiz API response: {error_detail}")
                logger.error(f"Request payload was: {payload}")
                raise
            except httpx.HTTPError as e:
                logger.error(f"Failed to initiate call: {str(e)}")
                raise
    
    async def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        """Retrieve call details from Vobiz.ai.
        
        Args:
            call_sid: Call identifier
            
        Returns:
            Call details
        """
        endpoint = f"{self.base_url}/api/v1/Account/{self.auth_id}/Call/{call_sid}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
    
    async def hangup_call(self, call_sid: str) -> Dict[str, Any]:
        """Hangup an active call.
        
        Args:
            call_sid: Call identifier
            
        Returns:
            API response
        """
        endpoint = f"{self.base_url}/api/v1/Account/{self.auth_id}/Call/{call_sid}"
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(endpoint, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            return response.json()


# Global client instance
vobiz_client = VobizClient()
