"""
Main entry point for the CSV Uploader FastAPI application.
Configures routes for health checks and file operations.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.db.mongo import db_manager
from app.api.v1.endpoints import files, health
from app.core.middleware import RequestLogMiddleware


# Initialize Scheduler
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Connect DB
    db_manager.connect()

    # 2. Startup: Configure and Start Scheduler
    # Run cleanup check every 60 minutes
    scheduler.add_job(
        delete_expired_files,
        trigger=IntervalTrigger(minutes=60),
        id="lgpd_cleanup_job",
        replace_existing=True,
    )
    scheduler.start()

    yield

    # 3. Shutdown: Clean up
    scheduler.shutdown()
    db_manager.close()


app = FastAPI(
    title=settings.PROJECT_NAME, lifespan=lifespan, version="1.1.0"  # Version bump
)

app.add_middleware(RequestLogMiddleware)

# Configure CORS
# WARNING: In production, replace ["*"] with specific domains (e.g., ["https://my-frontend.com"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"] # Crucial for download filenames
)

# Router Registration
app.include_router(
    health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health"]
)
app.include_router(files.router, prefix=f"{settings.API_V1_STR}/files", tags=["Files"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
