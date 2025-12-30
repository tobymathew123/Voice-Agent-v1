"""XML response builder for Vobiz.ai telephony apps."""

from typing import Optional, List
from xml.etree.ElementTree import Element, SubElement, tostring


class VobizXMLResponse:
    """Builder for Vobiz.ai XML responses (TwiML-compatible)."""
    
    def __init__(self):
        """Initialize XML response with root element."""
        self.root = Element("Response")
    
    def say(
        self,
        text: str,
        voice: str = "en-IN-Neural2-A",
        language: str = "en-IN"
    ) -> "VobizXMLResponse":
        """Add text-to-speech instruction.
        
        Args:
            text: Text to speak
            voice: Voice identifier
            language: Language code
        """
        say_elem = SubElement(self.root, "Say")
        say_elem.set("voice", voice)
        say_elem.set("language", language)
        say_elem.text = text
        return self
    
    def play(self, url: str) -> "VobizXMLResponse":
        """Play audio file from URL.
        
        Args:
            url: Audio file URL
        """
        play_elem = SubElement(self.root, "Play")
        play_elem.text = url
        return self
    
    def gather(
        self,
        action: str,
        method: str = "POST",
        timeout: int = 5,
        num_digits: Optional[int] = None,
        finish_on_key: str = "#",
        input_type: str = "dtmf speech"
    ) -> "VobizXMLResponse":
        """Gather user input (DTMF or speech).
        
        Args:
            action: Webhook URL to send results
            method: HTTP method
            timeout: Seconds to wait for input
            num_digits: Expected number of digits (for DTMF)
            finish_on_key: Key to end input
            input_type: Input types to accept (dtmf, speech, or both)
        """
        gather_elem = SubElement(self.root, "Gather")
        gather_elem.set("action", action)
        gather_elem.set("method", method)
        gather_elem.set("timeout", str(timeout))
        gather_elem.set("input", input_type)
        gather_elem.set("finishOnKey", finish_on_key)
        
        if num_digits:
            gather_elem.set("numDigits", str(num_digits))
        
        return self
    
    def gather_with_prompt(
        self,
        prompt_text: str,
        action: str,
        method: str = "POST",
        timeout: int = 5,
        input_type: str = "speech"
    ) -> "VobizXMLResponse":
        """Gather input with a spoken prompt.
        
        Args:
            prompt_text: Text to speak before gathering
            action: Webhook URL to send results
            method: HTTP method
            timeout: Seconds to wait for input
            input_type: Input types to accept
        """
        gather_elem = SubElement(self.root, "Gather")
        gather_elem.set("action", action)
        gather_elem.set("method", method)
        gather_elem.set("timeout", str(timeout))
        gather_elem.set("input", input_type)
        
        # Add Say element inside Gather
        say_elem = SubElement(gather_elem, "Say")
        say_elem.set("voice", "en-IN-Neural2-A")
        say_elem.set("language", "en-IN")
        say_elem.text = prompt_text
        
        return self
    
    def record(
        self,
        action: str,
        method: str = "POST",
        max_length: int = 120,
        finish_on_key: str = "#",
        transcribe: bool = False
    ) -> "VobizXMLResponse":
        """Record caller audio.
        
        Args:
            action: Webhook URL to send recording
            method: HTTP method
            max_length: Maximum recording duration in seconds
            finish_on_key: Key to stop recording
            transcribe: Whether to transcribe recording
        """
        record_elem = SubElement(self.root, "Record")
        record_elem.set("action", action)
        record_elem.set("method", method)
        record_elem.set("maxLength", str(max_length))
        record_elem.set("finishOnKey", finish_on_key)
        record_elem.set("transcribe", "true" if transcribe else "false")
        return self
    
    def redirect(self, url: str, method: str = "POST") -> "VobizXMLResponse":
        """Redirect call flow to another URL.
        
        Args:
            url: Webhook URL to redirect to
            method: HTTP method
        """
        redirect_elem = SubElement(self.root, "Redirect")
        redirect_elem.set("method", method)
        redirect_elem.text = url
        return self
    
    def hangup(self) -> "VobizXMLResponse":
        """End the call."""
        SubElement(self.root, "Hangup")
        return self
    
    def pause(self, length: int = 1) -> "VobizXMLResponse":
        """Add a pause.
        
        Args:
            length: Pause duration in seconds
        """
        pause_elem = SubElement(self.root, "Pause")
        pause_elem.set("length", str(length))
        return self
    
    def build(self) -> str:
        """Build and return XML string.
        
        Returns:
            XML string with proper declaration
        """
        xml_bytes = tostring(self.root, encoding="utf-8", method="xml")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes.decode("utf-8")


def create_welcome_response(callback_url: str) -> str:
    """Create a welcome message with speech gathering.
    
    Args:
        callback_url: URL to send speech results
        
    Returns:
        XML response string
    """
    return (
        VobizXMLResponse()
        .gather_with_prompt(
            prompt_text="Welcome to our service. How may I help you today?",
            action=callback_url,
            timeout=5,
            input_type="speech"
        )
        .say("I didn't catch that. Please try again.")
        .redirect(callback_url)
        .build()
    )


def create_error_response(error_message: str = "We're experiencing technical difficulties.") -> str:
    """Create an error response.
    
    Args:
        error_message: Message to speak to caller
        
    Returns:
        XML response string
    """
    return (
        VobizXMLResponse()
        .say(error_message)
        .say("Please try again later. Goodbye.")
        .hangup()
        .build()
    )


def create_goodbye_response(message: str = "Thank you for calling. Goodbye.") -> str:
    """Create a goodbye response.
    
    Args:
        message: Farewell message
        
    Returns:
        XML response string
    """
    return (
        VobizXMLResponse()
        .say(message)
        .hangup()
        .build()
    )
