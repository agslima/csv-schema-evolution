"""
Health check API endpoints.
"""

from fastapi import APIRouter, Response, status

from app.db.mongo import db_manager

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Liveness check (legacy path) to verify the service is running.

    Returns:
        dict: A dictionary containing the service status.
    """
    return {"status": "ok"}


@router.get("/live")
async def liveness_check():
    """
    Liveness check to verify the service is running.
    """
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check(response: Response):
    """
    Readiness check to verify MongoDB and GridFS availability.
    """
    dependencies = {
        "mongo": {"status": "error"},
        "gridfs": {"status": "error"},
    }
    ready = True

    if db_manager.db is None:
        dependencies["mongo"] = {"status": "error", "detail": "not initialized"}
        ready = False
    else:
        try:
            await db_manager.db.command("ping")
            dependencies["mongo"] = {"status": "ok"}
        # pylint: disable=broad-except
        except Exception as exc:
            dependencies["mongo"] = {"status": "error", "detail": str(exc)}
            ready = False

    if db_manager.fs_bucket is None:
        dependencies["gridfs"] = {"status": "error", "detail": "not initialized"}
        ready = False
    elif dependencies["mongo"]["status"] != "ok":
        dependencies["gridfs"] = {"status": "error", "detail": "mongo unavailable"}
        ready = False
    else:
        try:
            bucket_name = db_manager.fs_bucket.bucket_name
            await db_manager.db[f"{bucket_name}.files"].find_one({})
            dependencies["gridfs"] = {"status": "ok", "bucket": bucket_name}
        # pylint: disable=broad-except
        except Exception as exc:
            dependencies["gridfs"] = {"status": "error", "detail": str(exc)}
            ready = False

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "ok" if ready else "error", "dependencies": dependencies}
