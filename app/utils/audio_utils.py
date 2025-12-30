"""Audio format conversion and streaming utilities."""

import logging
from typing import Optional
import audioop
import wave
import io

logger = logging.getLogger(__name__)


class AudioConverter:
    """Utilities for audio format conversion for telephony."""
    
    @staticmethod
    def pcm_to_mulaw(pcm_data: bytes, sample_width: int = 2) -> bytes:
        """Convert PCM audio to μ-law encoding.
        
        Args:
            pcm_data: PCM audio bytes
            sample_width: Sample width in bytes (2 for 16-bit)
            
        Returns:
            μ-law encoded audio bytes
        """
        try:
            return audioop.lin2ulaw(pcm_data, sample_width)
        except Exception as e:
            logger.error(f"Error converting PCM to μ-law: {str(e)}")
            return pcm_data
    
    @staticmethod
    def mulaw_to_pcm(mulaw_data: bytes, sample_width: int = 2) -> bytes:
        """Convert μ-law audio to PCM encoding.
        
        Args:
            mulaw_data: μ-law audio bytes
            sample_width: Target sample width in bytes
            
        Returns:
            PCM audio bytes
        """
        try:
            return audioop.ulaw2lin(mulaw_data, sample_width)
        except Exception as e:
            logger.error(f"Error converting μ-law to PCM: {str(e)}")
            return mulaw_data
    
    @staticmethod
    def resample_audio(
        audio_data: bytes,
        from_rate: int,
        to_rate: int,
        sample_width: int = 2,
        channels: int = 1
    ) -> bytes:
        """Resample audio to different sample rate.
        
        Args:
            audio_data: Audio bytes
            from_rate: Source sample rate
            to_rate: Target sample rate
            sample_width: Sample width in bytes
            channels: Number of channels
            
        Returns:
            Resampled audio bytes
        """
        try:
            return audioop.ratecv(
                audio_data,
                sample_width,
                channels,
                from_rate,
                to_rate,
                None
            )[0]
        except Exception as e:
            logger.error(f"Error resampling audio: {str(e)}")
            return audio_data
    
    @staticmethod
    def create_wav_header(
        sample_rate: int = 8000,
        channels: int = 1,
        sample_width: int = 2,
        data_size: int = 0
    ) -> bytes:
        """Create WAV file header.
        
        Args:
            sample_rate: Sample rate in Hz
            channels: Number of channels
            sample_width: Sample width in bytes
            data_size: Size of audio data in bytes
            
        Returns:
            WAV header bytes
        """
        # RIFF header
        header = b'RIFF'
        header += (36 + data_size).to_bytes(4, 'little')
        header += b'WAVE'
        
        # fmt chunk
        header += b'fmt '
        header += (16).to_bytes(4, 'little')  # Chunk size
        header += (1).to_bytes(2, 'little')   # Audio format (PCM)
        header += channels.to_bytes(2, 'little')
        header += sample_rate.to_bytes(4, 'little')
        header += (sample_rate * channels * sample_width).to_bytes(4, 'little')  # Byte rate
        header += (channels * sample_width).to_bytes(2, 'little')  # Block align
        header += (sample_width * 8).to_bytes(2, 'little')  # Bits per sample
        
        # data chunk
        header += b'data'
        header += data_size.to_bytes(4, 'little')
        
        return header


class AudioStreamBuffer:
    """Buffer for streaming audio chunks."""
    
    def __init__(self, chunk_size: int = 8192):
        """Initialize audio buffer.
        
        Args:
            chunk_size: Size of audio chunks in bytes
        """
        self.chunk_size = chunk_size
        self.buffer = bytearray()
    
    def add_chunk(self, chunk: bytes):
        """Add audio chunk to buffer.
        
        Args:
            chunk: Audio bytes
        """
        self.buffer.extend(chunk)
    
    def get_chunk(self) -> Optional[bytes]:
        """Get next chunk from buffer.
        
        Returns:
            Audio chunk or None if buffer empty
        """
        if len(self.buffer) >= self.chunk_size:
            chunk = bytes(self.buffer[:self.chunk_size])
            self.buffer = self.buffer[self.chunk_size:]
            return chunk
        return None
    
    def get_all(self) -> bytes:
        """Get all buffered audio.
        
        Returns:
            All buffered audio bytes
        """
        data = bytes(self.buffer)
        self.buffer.clear()
        return data
    
    def clear(self):
        """Clear buffer."""
        self.buffer.clear()
    
    @property
    def size(self) -> int:
        """Get current buffer size in bytes."""
        return len(self.buffer)


def validate_telephony_audio(
    audio_data: bytes,
    expected_encoding: str = "mulaw",
    expected_rate: int = 8000
) -> bool:
    """Validate audio format for telephony compatibility.
    
    Args:
        audio_data: Audio bytes
        expected_encoding: Expected encoding
        expected_rate: Expected sample rate
        
    Returns:
        True if valid, False otherwise
    """
    # Basic validation - check if data exists
    if not audio_data or len(audio_data) == 0:
        logger.warning("Empty audio data")
        return False
    
    # For μ-law at 8kHz, typical duration should be reasonable
    # 8000 samples/sec, 1 byte per sample for μ-law
    duration_seconds = len(audio_data) / expected_rate
    
    if duration_seconds < 0.1:
        logger.warning(f"Audio too short: {duration_seconds}s")
        return False
    
    if duration_seconds > 300:  # 5 minutes max
        logger.warning(f"Audio too long: {duration_seconds}s")
        return False
    
    logger.info(f"Audio validated: {len(audio_data)} bytes, ~{duration_seconds:.2f}s")
    return True
