"""
Module for handling file storage operations using GridFS and MongoDB.
Provides functionality to save, retrieve, and delete files.
"""

import re
from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from fastapi import UploadFile, HTTPException
from app.db.mongo import db_manager
from app.core.config import settings
from app.core.security import encrypt_data, decrypt_data

# 1. Allow only safe characters (Alphanumeric, dot, dash, underscore, space)
FILENAME_REGEX = re.compile(r"^[a-zA-Z0-9\.\-\_ ]+$")


async def save_file_to_gridfs(file: UploadFile) -> ObjectId:
    """
    Reads the file stream, encrypts it, and saves it to MongoDB GridFS.
    """
    content = await file.read()

    if len(content) > settings.max_file_size_bytes:
        raise ValueError(f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB")

    # Encrypt content before storage
    encrypted_content = encrypt_data(content)

    # Open upload stream
    grid_in = db_manager.fs_bucket.open_upload_stream(file.filename)
    await grid_in.write(encrypted_content)
    await grid_in.close()

    # pylint: disable=protected-access
    return grid_in._id


async def create_file_metadata(file_id: ObjectId, filename: str) -> dict:
    """Creates the initial metadata document in the 'files' collection."""
    file_doc = {
        "_id": file_id,
        "filename": filename,
        "status": "pending",
        "fields": [],
        "records_count": 0,
        "created_at": datetime.now(timezone.utc),
    }
    await db_manager.db.files.insert_one(file_doc)
    return file_doc


async def get_file_content_as_string(file_id: str) -> str:
    """Retrieves file bytes from GridFS, decrypts, and decodes to string."""
    try:
        oid = ObjectId(file_id)
        grid_out = await db_manager.fs_bucket.open_download_stream(oid)
        encrypted_content = await grid_out.read()

        decrypted_content = decrypt_data(encrypted_content)

        return decrypted_content.decode("utf-8-sig")
    except Exception as e:
        raise ValueError(f"Could not read/decrypt file from storage: {e}") from e


async def update_file_status(
    file_id: str,
    status: str,
    fields: Optional[List[str]] = None,
    count: Optional[int] = 0,
    error_msg: Optional[str] = None,
) -> None:
    """
    Updates the file processing status, fields, count, and error messages.
    """
    update_data = {"status": status}

    if fields is not None:
        update_data["fields"] = fields
    if count is not None:
        update_data["records_count"] = count
    if error_msg:
        update_data["error_message"] = error_msg

    await db_manager.db.files.update_one(
        {"_id": ObjectId(file_id)},
        {"$set": update_data},
    )


async def delete_file(file_id: str) -> bool:
    """Deletes metadata and GridFS chunks."""
    oid = ObjectId(file_id)
    result = await db_manager.db.files.delete_one({"_id": oid})

    if result.deleted_count == 0:
        return False

    await db_manager.fs_bucket.delete(oid)
    return True
