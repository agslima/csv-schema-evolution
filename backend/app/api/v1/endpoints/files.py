"""
API endpoints for file management.
Handles file upload, listing, downloading, and deletion operations.
"""

# --- ADD THESE TWO LINES ---
import csv
from io import StringIO

# ---------------------------

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
        None, description="Optional field to help detect record grouping"
    ),
):
    # ... (Keep existing upload logic) ...
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Invalid file extension. Only .csv allowed."
        )

    file_id = None
    try:
        file_id = await storage.save_file_to_gridfs(file)
        await storage.create_file_metadata(file_id, file.filename)
        content_str = await storage.get_file_content_as_string(str(file_id))
        records, fields = await csv_handler.process_csv_content(content_str, id_field)

        await storage.update_file_status(
            str(file_id), status="processed", fields=fields, count=len(records)
        )

        return {
            "id": str(file_id),
            "filename": file.filename,
            "status": "processed",
            "records_count": len(records),
            "fields": fields,
        }

    except ValueError as e:
        if file_id:
            await storage.update_file_status(
                str(file_id), status="error", error_msg=str(e)
            )
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception as e:
        if file_id:
            await storage.update_file_status(
                str(file_id), status="error", error_msg="Internal Processing Error"
            )
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}"
        ) from e


@router.get("/")
async def list_files():
    # ... (Keep existing list logic) ...
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
                "error_message": doc.get("error_message"),
            }
        )
    return results


@router.get("/{file_id}/download")
async def download_file(file_id: str):
    """
    Downloads the processed/cleaned CSV file.
    """
    try:
        doc = await db_manager.db.files.find_one({"_id": ObjectId(file_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="File not found")

        raw_content = await storage.get_file_content_as_string(file_id)

        # Re-Run Processing
        records, fields = await csv_handler.process_csv_content(raw_content)

        # Convert back to CSV
        output = StringIO()  # <--- This line caused the error before!
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
        clean_csv_content = output.getvalue()

        return StreamingResponse(
            iter([clean_csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=cleaned_{doc['filename']}"
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating download: {e}"
        ) from e


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    # ... (Keep existing delete logic) ...
    success = await storage.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted", "id": file_id}
