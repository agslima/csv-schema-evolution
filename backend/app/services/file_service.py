"""
Service layer for file operations.
Orchestrates storage and CSV processing.
"""

import csv
from io import StringIO
from typing import Optional, List, Dict, Tuple

from fastapi import UploadFile

from app.repositories import file_repository
from app.services import csv_handler


def _build_sanitized_csv(records: List[Dict], fields: List[str]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


async def save_upload(file: UploadFile, id_field: Optional[str] = None) -> Dict:
    """
    Saves an uploaded CSV, processes schema, and updates metadata.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValueError("Invalid file extension. Only .csv allowed.")

    file_id = None
    try:
        content = await file.read()
        file_id = await file_repository.save_file(content, file.filename)
        await file_repository.create_file_metadata(file_id, file.filename)
        try:
            content_str = content.decode("utf-8-sig")
        except Exception as e:
            raise ValueError(f"Could not decode file content: {e}") from e

        records, fields = await csv_handler.process_csv_content(content_str, id_field)
        clean_csv_content = _build_sanitized_csv(records, fields)
        processed_file_id = await file_repository.save_processed_file(
            clean_csv_content.encode("utf-8"), file.filename
        )

        await file_repository.update_file_status(
            str(file_id),
            status="processed",
            fields=fields,
            count=len(records),
            processed_fs_id=processed_file_id,
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
            await file_repository.update_file_status(
                str(file_id), status="error", error_msg=str(e)
            )
        raise

    except Exception:
        if file_id:
            await file_repository.update_file_status(
                str(file_id), status="error", error_msg="Internal Processing Error"
            )
        raise


async def list_files() -> List[Dict]:
    """
    Lists all uploaded files sorted by creation date (newest first).
    """
    docs = await file_repository.list_files()
    results = []
    for doc in docs:
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


async def download_processed_file(file_id: str) -> Tuple[bytes, str]:
    """
    Returns the stored sanitized CSV bytes and original filename.
    """
    doc = await file_repository.get_file_metadata(file_id)
    if not doc:
        raise FileNotFoundError("File not found")

    processed_fs_id = doc.get("processed_fs_id")
    if processed_fs_id:
        processed_content = await file_repository.get_file_content_as_bytes(
            processed_fs_id
        )
        return processed_content, doc["filename"]

    raw_content = await file_repository.get_file_content_as_string(file_id)

    records, fields = await csv_handler.process_csv_content(raw_content)

    clean_csv_content = _build_sanitized_csv(records, fields)
    processed_bytes = clean_csv_content.encode("utf-8")
    processed_file_id = await file_repository.save_processed_file(
        processed_bytes, doc["filename"]
    )
    await file_repository.update_file_status(
        file_id,
        status="processed",
        fields=fields,
        count=len(records),
        processed_fs_id=processed_file_id,
    )

    return processed_bytes, doc["filename"]


async def delete_file(file_id: str) -> bool:
    """
    Deletes a file and its metadata from the database.
    """
    return await file_repository.delete_file(file_id)
