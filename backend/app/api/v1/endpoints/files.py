"""
API endpoints for file management.
Handles file upload, listing, downloading, and deletion operations.
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.services import file_service

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    id_field: Optional[str] = Query(
        None, description="Optional field to help detect record grouping"
    ),
):
    """
    Uploads a CSV file, saves raw content, processes schema, and returns metadata.
    """
    try:
        return await file_service.save_upload(file, id_field)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except Exception as err:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(err)}"
        ) from err


@router.get("/")
async def list_files():
    """
    Lists all uploaded files sorted by creation date (newest first).
    """
    return await file_service.list_files()


@router.get("/{file_id}/download")
async def download_file(file_id: str):
    """
    Downloads the processed (safe) CSV file.
    Streams the stored sanitized CSV instead of re-parsing on download.
    """
    try:
        clean_csv_bytes, filename = await file_service.download_processed_file(
            file_id
        )
        return StreamingResponse(
            iter([clean_csv_bytes]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=cleaned_{filename}"},
        )
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail="File not found") from err
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=500, detail=f"Error generating download: {err}"
        ) from err


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Deletes a file and its metadata from the database.
    """
    success = await file_service.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted", "id": file_id}
