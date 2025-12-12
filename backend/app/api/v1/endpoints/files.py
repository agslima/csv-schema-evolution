"""
API endpoints for file management.
Handles file upload, listing, downloading, and deletion operations.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status
from fastapi.responses import JSONResponse
from typing import List, Optional

from app.services import storage, csv_handler
from app.utils.validators import validate_csv_extension  # Assuming you have this helper

# If not, a simple inline check works, but let's assume strict separation.

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
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Invalid file extension. Only .csv allowed."
        )

    try:
        # 1. Save binary to GridFS
        file_id = await storage.save_file_to_gridfs(file)

        # 2. Create metadata entry
        await storage.create_file_metadata(file_id, file.filename)

        # 3. Process Content (Read -> Parse -> Sanitize)
        # Note: For very large files, this should be offloaded to a background task (Celery/RabbitMQ)
        content_str = await storage.get_file_content_as_string(str(file_id))
        records, fields = await csv_handler.process_csv_content(content_str, id_field)

        # 4. Update Metadata
        await storage.update_file_status(str(file_id), fields, len(records))

        return {
            "id": str(file_id),
            "filename": file.filename,
            "status": "processed",
            "records_count": len(records),
            "fields": fields,
            # "data": records  <-- Uncomment if you want to return data immediately
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the actual error internally
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.delete("/{file_id}", status_code=status.HTTP_200_OK)
async def delete_file(file_id: str):
    """Deletes a file and its metadata."""
    success = await storage.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted", "id": file_id}
