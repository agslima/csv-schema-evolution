"""
API endpoints for file management.
Handles file upload, listing, downloading, and deletion operations.
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from bson import ObjectId

# --- FIX: Import storage from 'utils' and csv_handler from 'services' ---
from app.utils import storage
from app.services import csv_handler
from app.db.mongo import db_manager

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
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}"
        ) from e


@router.get("/")
async def list_files():
    """
    Lists all uploaded files sorted by creation date (newest first).
    """
    cursor = db_manager.db.files.find().sort("created_at", -1)

    results = []
    async for doc in cursor:
        results.append(
            {
                "id": str(doc["_id"]),
                "filename": doc.get("filename"),
                "status": doc.get("status"),
                "records_count": doc.get("records_count", 0),
                "fields": doc.get("fields", []),
                "created_at": doc.get("created_at"),
            }
        )
    return results


@router.get("/{file_id}/download")
async def download_file(file_id: str):
    """
    Downloads the original CSV file.
    """
    try:
        # Verify existence
        doc = await db_manager.db.files.find_one({"_id": ObjectId(file_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="File not found")

        # Get content (Decrypted)
        content_str = await storage.get_file_content_as_string(file_id)

        # Stream it back
        return StreamingResponse(
            iter([content_str]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={doc['filename']}"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"File not found or error reading: {e}"
        ) from e


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Deletes a file and its metadata."""
    success = await storage.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted", "id": file_id}
