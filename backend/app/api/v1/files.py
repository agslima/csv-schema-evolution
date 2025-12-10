"""
API endpoints for file management.
Handles file upload, listing, downloading, and deletion operations.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

# Internal application imports
from app.services import storage, csv_processor
from app.models.file_models import FileResponse
from app.utils.validators import validate_csv_file
from app.db.mongo import db

router = APIRouter()


@router.post("/upload", response_model=FileResponse)
async def upload_file(file: UploadFile = File(...), id_field: str = None):
    """
    Uploads a CSV file, saves it to storage, and initiates processing.
    """
    validate_csv_file(file)
    file_id = await storage.save_file(file)
    await csv_processor.process_csv(str(file_id), id_field)
    doc = await storage.get_file_stream(str(file_id))

    # doc is a tuple (stream, metadata), we access metadata at index 1
    return {
        "id": str(file_id),
        "filename": file.filename,
        "status": "processed",
        "records_count": doc[1]["records_count"],
        "fields": doc[1]["fields"],
    }


@router.get("/")
async def list_files():
    """
    Lists all uploaded files sorted by creation date.
    """
    cursor = db.files.find().sort("created_at", -1)
    results = []
    async for doc in cursor:
        results.append(
            {
                "id": str(doc["_id"]),
                "filename": doc["filename"],
                "status": doc.get("status"),
                "records_count": doc.get("records_count", 0),
                "fields": doc.get("fields", []),
            }
        )
    return results


@router.get("/{file_id}/download")
async def download_file(file_id: str):
    """
    Downloads the original CSV file.
    """
    cursor_doc = await storage.get_file_stream(file_id)
    if not cursor_doc:
        raise HTTPException(404, "File not found")
    stream, doc = cursor_doc
    return StreamingResponse(
        stream,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={doc['filename']}"},
    )


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Deletes a file from storage and database.
    """
    success = await storage.delete_file(file_id)
    if not success:
        raise HTTPException(404, "File not found")
    return {"status": "deleted"}
