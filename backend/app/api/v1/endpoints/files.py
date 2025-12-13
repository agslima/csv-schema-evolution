"""
API endpoints for file management.
Handles file upload, listing, downloading, and deletion operations.
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status

# FIX: Import storage from utils, not services
from app.utils import storage
from app.services import csv_handler

# FIX: Import the correct validator function name
from app.utils.validators import validate_csv_file

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    id_field: Optional[str] = Query(
        None, description="Optional field to group records"
    ),
):
    """
    Uploads a CSV, saves to GridFS, processes content, and returns metadata.
    """
    # 1. Validation (Delegate to utility)
    validate_csv_file(file)

    try:
        # 2. Save binary to GridFS (Encrypts automatically)
        file_id = await storage.save_file_to_gridfs(file)

        # 3. Create metadata entry
        await storage.create_file_metadata(file_id, file.filename)

        # 4. Process Content (Read -> Parse -> Sanitize)
        # Note: For very large files, offload to background task (Celery/RabbitMQ)
        content_str = await storage.get_file_content_as_string(str(file_id))
        records, fields = await csv_handler.process_csv_content(content_str, id_field)

        # 5. Update Metadata
        await storage.update_file_status(str(file_id), fields, len(records))

        return {
            "id": str(file_id),
            "filename": file.filename,
            "status": "processed",
            "records_count": len(records),
            "fields": fields,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        # Log the actual error internally before raising HTTP error
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}"
        ) from e


@router.delete("/{file_id}", status_code=status.HTTP_200_OK)
async def delete_file(file_id: str):
    """Deletes a file and its metadata."""
    success = await storage.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted", "id": file_id}
