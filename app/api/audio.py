"""Audio file serving endpoint."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Audio cache directory
AUDIO_CACHE_DIR = Path("audio_cache")


@router.get("/{filename}")
async def serve_audio_file(filename: str):
    """Serve audio file for telephony playback.
    
    Args:
        filename: Audio filename
        
    Returns:
        Audio file response
    """
    try:
        file_path = AUDIO_CACHE_DIR / filename
        
        if not file_path.exists():
            logger.warning(f"Audio file not found: {filename}")
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Verify file is within cache directory (security)
        if not file_path.resolve().is_relative_to(AUDIO_CACHE_DIR.resolve()):
            logger.error(f"Attempted path traversal: {filename}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        logger.info(f"Serving audio file: {filename}")
        
        return FileResponse(
            path=str(file_path),
            media_type="audio/wav",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
