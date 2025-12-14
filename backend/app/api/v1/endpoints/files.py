"""
API endpoints for file management.
Handles file upload, listing, downloading, and deletion operations.
"""

import csv
from io import StringIO
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from bson import ObjectId

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
    Uploads a CSV, Sanitizes content, saves the CLEAN version to GridFS,
    and returns metadata.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Invalid file extension. Only .csv allowed."
        )

    try:
        # 1. Read the raw content immediately (Into Memory)
        content_bytes = await file.read()
        try:
            content_str = content_bytes.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=400, detail="Invalid CSV encoding. Use UTF-8."
            ) from e

        # 2. Process & Sanitize (In Memory)
        # This strips formula injections and normalizes data
        # Note: We rely on csv_handler logic to return sanitized dictionaries
        records, fields = await csv_handler.process_csv_content(content_str, id_field)

        # 3. Reconstruct the CSV (The "Evolution" Step)
        # We create a new, clean CSV string from the sanitized records.
        # This ensures the stored file is safe to download.
        output_io = StringIO()
        if fields:
            # We use standard Excel-compatible CSV format
            writer = csv.DictWriter(output_io, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)

        # Convert the clean CSV string back to bytes for storage
        sanitized_content = output_io.getvalue().encode("utf-8")

        # 4. Save the SANITIZED content to GridFS
        file_id = await storage.save_bytes_to_gridfs(sanitized_content, file.filename)

        # 5. Create metadata entry
        await storage.create_file_metadata(file_id, file.filename)

        # 6. Update Metadata status
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
    Downloads the processed (safe) CSV file.
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
