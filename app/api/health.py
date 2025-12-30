"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "ai-voice-agent"}


@router.get("/ready")
async def readiness_check():
    """Readiness check for dependent services."""
    # TODO: Check Deepgram, OpenAI, Vobiz connectivity
    return {"status": "ready"}
