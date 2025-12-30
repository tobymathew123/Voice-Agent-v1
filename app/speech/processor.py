"""Speech processing abstraction layer for telephony.

This module provides clean separation between telephony logic and speech processing.
Telephony handlers call these abstractions without Deepgram-specific knowledge.
"""

import logging
from typing import Optional
from pathlib import Path

from app.speech.stt import deepgram_stt_simple, DeepgramSTT
from app.speech.tts import deepgram_tts, TTSVoiceConfig
from app.utils.audio_utils import validate_telephony_audio

logger = logging.getLogger(__name__)


class SpeechProcessor:
    """High-level speech processing interface for telephony.
    
    Abstracts Deepgram implementation details from telephony layer.
    """
    
    @staticmethod
    async def transcribe_audio_url(audio_url: str, language: str = "en-IN") -> Optional[str]:
        """Transcribe audio from URL.
        
        Args:
            audio_url: URL to audio file (e.g., Vobiz recording URL)
            language: Language code
            
        Returns:
            Transcribed text or None
        """
        try:
            logger.info(f"Transcribing audio from URL: {audio_url}")
            transcript = await deepgram_stt_simple.transcribe_url(audio_url)
            return transcript
        except Exception as e:
            logger.error(f"Error transcribing audio URL: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    async def generate_speech(
        text: str,
        language: str = "en-IN",
        cache: bool = True
    ) -> Optional[str]:
        """Generate speech audio from text.
        
        Args:
            text: Text to synthesize
            language: Language code (determines voice selection)
            cache: Whether to cache generated audio
            
        Returns:
            Path to audio file or None
        """
        try:
            # Sanitize text for TTS (remove symbols, abbreviations)
            sanitized_text = SpeechProcessor._sanitize_text_for_tts(text)
            
            # Get appropriate voice for language
            voice = TTSVoiceConfig.get_voice_for_language(language)
            
            logger.info(f"Generating speech: '{sanitized_text[:50]}...' in {language}")
            
            audio_path = await deepgram_tts.synthesize(
                text=sanitized_text,
                cache=cache,
                voice_override=voice
            )
            
            if audio_path:
                logger.info(f"Speech generated: {audio_path}")
            
            return audio_path
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    async def generate_speech_streaming(
        text: str,
        language: str = "en-IN"
    ) -> Optional[bytes]:
        """Generate speech audio as bytes (streaming).
        
        Args:
            text: Text to synthesize
            language: Language code
            
        Returns:
            Audio bytes or None
        """
        try:
            sanitized_text = SpeechProcessor._sanitize_text_for_tts(text)
            voice = TTSVoiceConfig.get_voice_for_language(language)
            
            audio_bytes = await deepgram_tts.synthesize_streaming(
                text=sanitized_text,
                voice_override=voice
            )
            
            if audio_bytes and validate_telephony_audio(audio_bytes):
                return audio_bytes
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating streaming speech: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def _sanitize_text_for_tts(text: str) -> str:
        """Sanitize text for TTS synthesis.
        
        Removes or expands abbreviations, symbols, etc. for clear pronunciation.
        
        Args:
            text: Raw text
            
        Returns:
            Sanitized text
        """
        # Basic sanitization
        sanitized = text.strip()
        
        # Expand common abbreviations for Indian context
        replacements = {
            "OTP": "O T P",
            "KYC": "K Y C",
            "PAN": "P A N",
            "GST": "G S T",
            "UPI": "U P I",
            "NEFT": "N E F T",
            "RTGS": "R T G S",
            "IFSC": "I F S C",
            "Rs.": "Rupees",
            "₹": "Rupees",
            "&": "and",
        }
        
        for abbr, expansion in replacements.items():
            sanitized = sanitized.replace(abbr, expansion)
        
        return sanitized
    
    @staticmethod
    def get_audio_url_for_playback(audio_path: str, base_url: str) -> str:
        """Convert local audio path to publicly accessible URL.
        
        Args:
            audio_path: Local file path
            base_url: Base URL of the server
            
        Returns:
            Public URL for audio playback
        """
        # Extract filename from path
        filename = Path(audio_path).name
        
        # Construct public URL
        # Assumes audio files are served from /audio/ endpoint
        return f"{base_url}/audio/{filename}"


# Convenience functions for telephony handlers
async def transcribe_call_recording(recording_url: str) -> Optional[str]:
    """Transcribe call recording from Vobiz.
    
    Args:
        recording_url: Vobiz recording URL
        
    Returns:
        Transcript text
    """
    return await SpeechProcessor.transcribe_audio_url(recording_url)


async def generate_telephony_response(text: str, language: str = "en-IN") -> Optional[str]:
    """Generate speech response for telephony playback.
    
    Args:
        text: Response text
        language: Language code
        
    Returns:
        Path to audio file
    """
    return await SpeechProcessor.generate_speech(text, language, cache=True)
