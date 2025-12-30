"""FastAPI application entrypoint."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import telephony, health, outbound, audio, analytics

# Initialize FastAPI app
app = FastAPI(
    title="AI Voice Agent",
    description="Real-time AI voice agent for BFSI sector",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(telephony.router, prefix="/telephony", tags=["Telephony"])
app.include_router(outbound.router, prefix="/telephony/outbound", tags=["Outbound Calls"])
app.include_router(audio.router, prefix="/audio", tags=["Audio"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # TODO: Initialize database connections, cache, etc.
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # TODO: Close connections, cleanup resources
    pass


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
    )
