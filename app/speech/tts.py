"""Text-to-Speech service using Deepgram."""

import asyncio
import logging
from typing import Optional
import httpx
from pathlib import Path
import hashlib
import os

from deepgram import DeepgramClient, SpeakOptions

from app.config import settings

logger = logging.getLogger(__name__)


class DeepgramTTS:
    """Async Text-to-Speech using Deepgram Speak API.
    
    Generates telephony-compatible audio (μ-law, 8kHz) for PSTN playback.
    Supports configurable voices and multilingual synthesis.
    """
    
    def __init__(
        self,
        voice: str = "aura-asteria-en",
        encoding: str = "mulaw",
        sample_rate: int = 8000,
        container: str = "wav"
    ):
        """Initialize Deepgram TTS client.
        
        Args:
            voice: Voice model (configurable, not hardcoded)
                   Examples: aura-asteria-en, aura-athena-en, aura-luna-en
                   Note: Indian-accented voices may be selected when available
            encoding: Audio encoding (mulaw for telephony)
            sample_rate: Sample rate in Hz (8000 for PSTN)
            container: Audio container format (wav, mp3, etc.)
        """
        self.voice = voice
        self.encoding = encoding
        self.sample_rate = sample_rate
        self.container = container
        
        # Initialize Deepgram client
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        
        # Audio cache directory
        self.cache_dir = Path("audio_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    async def synthesize(
        self,
        text: str,
        cache: bool = True,
        voice_override: Optional[str] = None
    ) -> Optional[str]:
        """Synthesize speech from text.
        
        Args:
            text: Text to synthesize (must be language-safe, no abbreviations/symbols)
            cache: Whether to cache generated audio
            voice_override: Override default voice for this synthesis
            
        Returns:
            Path to generated audio file or None if error
        """
        try:
            # Validate text
            if not text or not text.strip():
                logger.warning("Empty text provided for TTS")
                return None
            
            # Use override voice if provided
            voice = voice_override or self.voice
            
            # Check cache
            if cache:
                cache_key = self._get_cache_key(text, voice)
                cached_file = self.cache_dir / f"{cache_key}.{self.container}"
                if cached_file.exists():
                    logger.info(f"Using cached audio: {cached_file}")
                    return str(cached_file)
            
            # Configure speak options
            options = SpeakOptions(
                model=voice,
                encoding=self.encoding,
                sample_rate=self.sample_rate,
                container=self.container
            )
            
            # Generate speech
            logger.info(f"Generating TTS: '{text[:50]}...' with voice {voice}")
            
            response = await self.client.speak.asyncrest.v("1").save(
                filename=str(cached_file) if cache else None,
                source={"text": text},
                options=options
            )
            
            if cache and cached_file.exists():
                logger.info(f"Audio generated and cached: {cached_file}")
                return str(cached_file)
            else:
                # If not caching, save to temp file
                temp_file = self.cache_dir / f"temp_{hashlib.md5(text.encode()).hexdigest()}.{self.container}"
                # Response should contain audio data
                logger.info(f"Audio generated: {temp_file}")
                return str(temp_file)
                
        except Exception as e:
            logger.error(f"Error generating TTS: {str(e)}", exc_info=True)
            return None
    
    async def synthesize_streaming(
        self,
        text: str,
        voice_override: Optional[str] = None
    ) -> Optional[bytes]:
        """Synthesize speech and return audio bytes directly.
        
        Args:
            text: Text to synthesize
            voice_override: Override default voice
            
        Returns:
            Audio bytes or None if error
        """
        try:
            if not text or not text.strip():
                return None
            
            voice = voice_override or self.voice
            
            options = SpeakOptions(
                model=voice,
                encoding=self.encoding,
                sample_rate=self.sample_rate,
                container=self.container
            )
            
            logger.info(f"Generating streaming TTS: '{text[:50]}...'")
            
            response = await self.client.speak.asyncrest.v("1").stream(
                source={"text": text},
                options=options
            )
            
            # Collect audio chunks
            audio_data = b""
            async for chunk in response:
                audio_data += chunk
            
            logger.info(f"Streaming TTS generated: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error generating streaming TTS: {str(e)}", exc_info=True)
            return None
    
    def _get_cache_key(self, text: str, voice: str) -> str:
        """Generate cache key for text and voice combination.
        
        Args:
            text: Text content
            voice: Voice model
            
        Returns:
            Cache key (hash)
        """
        content = f"{text}_{voice}_{self.encoding}_{self.sample_rate}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear audio cache directory."""
        try:
            for file in self.cache_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            logger.info("Audio cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")


class TTSVoiceConfig:
    """Voice configuration presets for different use cases.
    
    This allows easy switching between voices without hardcoding.
    Indian-accented or multilingual voices can be added here when available.
    """
    
    # English voices
    ENGLISH_NEUTRAL = "aura-asteria-en"
    ENGLISH_WARM = "aura-athena-en"
    ENGLISH_PROFESSIONAL = "aura-luna-en"
    
    # Note: Add Indian-accented voices when available from Deepgram
    # INDIAN_ENGLISH = "aura-indian-en"  # Example placeholder
    # HINDI = "aura-hindi"  # Example placeholder
    
    @classmethod
    def get_voice_for_language(cls, language: str) -> str:
        """Get appropriate voice for language code.
        
        Args:
            language: Language code (e.g., en-IN, hi-IN)
            
        Returns:
            Voice model name
        """
        # Map language codes to voices
        voice_map = {
            "en-IN": cls.ENGLISH_NEUTRAL,
            "en-US": cls.ENGLISH_PROFESSIONAL,
            "en-GB": cls.ENGLISH_WARM,
            # Add more mappings as voices become available
        }
        
        return voice_map.get(language, cls.ENGLISH_NEUTRAL)


# Global instance for convenience
# Voice can be changed per call or by creating new instances
deepgram_tts = DeepgramTTS(voice=TTSVoiceConfig.ENGLISH_NEUTRAL)
