"""
Health check API endpoint.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Perform a basic health check to verify the service is running.

    Returns:
        dict: A dictionary containing the service status.
    """
    return {"status": "ok"}
