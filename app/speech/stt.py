"""Speech-to-Text service using Deepgram."""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

from app.config import settings

logger = logging.getLogger(__name__)


class DeepgramSTT:
    """Async streaming Speech-to-Text using Deepgram WebSocket API.
    
    Designed for PSTN telephony with μ-law encoded audio at 8kHz.
    Supports long-lived, event-driven transcription per call session.
    """
    
    def __init__(
        self,
        language: str = "en-IN",
        model: str = "nova-2",
        encoding: str = "mulaw",
        sample_rate: int = 8000,
        channels: int = 1
    ):
        """Initialize Deepgram STT client.
        
        Args:
            language: Language code (e.g., en-IN, hi-IN, ml-IN)
            model: Deepgram model (nova-2 recommended)
            encoding: Audio encoding (mulaw for telephony)
            sample_rate: Sample rate in Hz (8000 for PSTN)
            channels: Number of audio channels (1 for mono)
        """
        self.language = language
        self.model = model
        self.encoding = encoding
        self.sample_rate = sample_rate
        self.channels = channels
        
        # Initialize Deepgram client
        config = DeepgramClientOptions(
            options={"keepalive": "true"}
        )
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY, config)
        
        # Connection state
        self.connection = None
        self.is_connected = False
        
        # Callbacks
        self.on_interim_transcript: Optional[Callable[[str], None]] = None
        self.on_final_transcript: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    async def start_stream(self) -> bool:
        """Start streaming connection to Deepgram.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Configure live transcription options
            options = LiveOptions(
                model=self.model,
                language=self.language,
                encoding=self.encoding,
                sample_rate=self.sample_rate,
                channels=self.channels,
                interim_results=True,
                punctuate=True,
                smart_format=True,
                utterance_end_ms=1000,
            )
            
            # Create live transcription connection
            self.connection = self.client.listen.asynclive.v("1")
            
            # Register event handlers
            self.connection.on(LiveTranscriptionEvents.Open, self._on_open)
            self.connection.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
            self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.connection.on(LiveTranscriptionEvents.Close, self._on_close)
            
            # Start connection
            if await self.connection.start(options):
                logger.info(f"Deepgram STT stream started: {self.language}, {self.encoding}, {self.sample_rate}Hz")
                return True
            else:
                logger.error("Failed to start Deepgram STT stream")
                return False
                
        except Exception as e:
            logger.error(f"Error starting Deepgram STT stream: {str(e)}", exc_info=True)
            return False
    
    async def send_audio(self, audio_chunk: bytes):
        """Send audio chunk to Deepgram for transcription.
        
        Args:
            audio_chunk: Raw audio bytes (μ-law encoded)
        """
        if self.connection and self.is_connected:
            try:
                self.connection.send(audio_chunk)
            except Exception as e:
                logger.error(f"Error sending audio to Deepgram: {str(e)}")
    
    async def stop_stream(self):
        """Stop streaming connection."""
        if self.connection:
            try:
                await self.connection.finish()
                logger.info("Deepgram STT stream stopped")
            except Exception as e:
                logger.error(f"Error stopping Deepgram STT stream: {str(e)}")
            finally:
                self.is_connected = False
                self.connection = None
    
    def _on_open(self, *args, **kwargs):
        """Handle connection open event."""
        self.is_connected = True
        logger.info("Deepgram STT connection opened")
    
    def _on_transcript(self, *args, **kwargs):
        """Handle transcript event."""
        try:
            result = kwargs.get("result")
            if not result:
                return
            
            # Extract transcript
            channel = result.channel
            if not channel or not channel.alternatives:
                return
            
            alternative = channel.alternatives[0]
            transcript = alternative.transcript
            
            if not transcript:
                return
            
            # Determine if interim or final
            is_final = result.is_final
            
            if is_final:
                logger.info(f"Final transcript: {transcript}")
                if self.on_final_transcript:
                    self.on_final_transcript(transcript)
            else:
                logger.debug(f"Interim transcript: {transcript}")
                if self.on_interim_transcript:
                    self.on_interim_transcript(transcript)
                    
        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}", exc_info=True)
    
    def _on_error(self, *args, **kwargs):
        """Handle error event."""
        error = kwargs.get("error")
        logger.error(f"Deepgram STT error: {error}")
        if self.on_error:
            self.on_error(str(error))
    
    def _on_close(self, *args, **kwargs):
        """Handle connection close event."""
        self.is_connected = False
        logger.info("Deepgram STT connection closed")


class DeepgramSTTSimple:
    """Simple non-streaming STT for pre-recorded audio or URLs.
    
    Use this for processing recorded audio files or audio URLs
    from telephony systems (e.g., Vobiz recordings).
    """
    
    def __init__(
        self,
        language: str = "en-IN",
        model: str = "nova-2"
    ):
        """Initialize simple STT client.
        
        Args:
            language: Language code (e.g., en-IN, hi-IN)
            model: Deepgram model
        """
        self.language = language
        self.model = model
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
    
    async def transcribe_url(self, audio_url: str) -> Optional[str]:
        """Transcribe audio from URL.
        
        Args:
            audio_url: URL to audio file
            
        Returns:
            Transcribed text or None if error
        """
        try:
            options = {
                "model": self.model,
                "language": self.language,
                "punctuate": True,
                "smart_format": True,
            }
            
            source = {"url": audio_url}
            
            response = await self.client.listen.asyncrest.v("1").transcribe_url(
                source, options
            )
            
            # Extract transcript
            if response.results and response.results.channels:
                channel = response.results.channels[0]
                if channel.alternatives:
                    transcript = channel.alternatives[0].transcript
                    logger.info(f"Transcribed URL: {transcript}")
                    return transcript
            
            return None
            
        except Exception as e:
            logger.error(f"Error transcribing URL: {str(e)}", exc_info=True)
            return None
    
    async def transcribe_file(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio from file data.
        
        Args:
            audio_data: Raw audio file bytes
            
        Returns:
            Transcribed text or None if error
        """
        try:
            options = {
                "model": self.model,
                "language": self.language,
                "punctuate": True,
                "smart_format": True,
            }
            
            response = await self.client.listen.asyncrest.v("1").transcribe_file(
                {"buffer": audio_data}, options
            )
            
            # Extract transcript
            if response.results and response.results.channels:
                channel = response.results.channels[0]
                if channel.alternatives:
                    transcript = channel.alternatives[0].transcript
                    logger.info(f"Transcribed file: {transcript}")
                    return transcript
            
            return None
            
        except Exception as e:
            logger.error(f"Error transcribing file: {str(e)}", exc_info=True)
            return None


# Global instances for convenience
# Language can be changed per call by creating new instances
deepgram_stt_simple = DeepgramSTTSimple(language="en-IN")
