"""
FILE: app/main.py
==================
WHAT THIS FILE DOES:
    This is the entry point of the entire JobSoccer AI Service.
    When the server starts (uvicorn app.main:app), execution begins here.
    This file creates the FastAPI application and registers all API routes.

    Think of it like the front door of a building. Anyone coming in from
    outside must pass through this door first. This file knows which room
    is where and sends each visitor (request) to the correct destination.

CONNECTED TO:
    → app/api/endpoints.py  : all API routes come from here
    → app/core/config.py    : project name is read from here
"""

from fastapi import FastAPI
from app.api.endpoints import router as api_router
from app.core.config import settings

# Create the FastAPI application instance.
# The title, description and version appear in the Swagger UI at /docs.
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "JobSoccer AI Service — the AI layer of the football recruitment platform. "
        "Handles audio transcription (Whisper) and role-specific "
        "interview evaluation (GPT-4o-mini)."
    ),
    version="1.0.0",
)

# Register all API routes under the /api/v1 prefix.
# Example: a route defined as "/roles" in endpoints.py becomes
# accessible as "/api/v1/roles" from outside.
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def read_root():
    """
    WHY THIS EXISTS:
        A simple health check endpoint to confirm the server is running.
        Backend developers or monitoring tools can hit this route to
        verify the AI service is alive before sending real requests.

    OUTPUT:
        {"message": "Welcome to JobSoccer AI API"}

    CALLED FROM:
        Directly from a browser or monitoring tool.
        No other Python file calls this function.
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}
