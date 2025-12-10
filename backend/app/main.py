"""
Main entry point for the CSV Uploader FastAPI application.
Configures routes for health checks and file operations.
"""

from fastapi import FastAPI
from app.api.v1 import files, health

app = FastAPI(title="CSV Uploader")

app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])