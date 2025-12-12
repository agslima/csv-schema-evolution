"""
Module for handling file storage operations using GridFS and MongoDB.
Provides functionality to save, retrieve, and delete files.
"""

from bson import ObjectId
from fastapi import UploadFile
from app.db.mongo import db_manager
from app.core.config import settings
from app.core.security import encrypt_data, decrypt_data
from datetime import datetime, timezone


async def save_file_to_gridfs(file: UploadFile) -> ObjectId:
    """
    Reads the file stream and saves it to MongoDB GridFS.

    Raises:
        ValueError: If file size exceeds the configured limit.
    """
    content = await file.read()

    if len(content) > settings.max_file_size_bytes:
        raise ValueError(f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB")

    # Reset cursor in case we need to read it again later (though we consumed it here)
    await file.seek(0)

    # Open upload stream
    grid_in = db_manager.fs_bucket.open_upload_stream(file.filename)
    await grid_in.write(content)
    await grid_in.close()

    return grid_in._id


async def create_file_metadata(file_id: ObjectId, filename: str) -> dict:
    """Creates the initial metadata document in the 'files' collection."""
    file_doc = {
        "_id": file_id,  # Link directly to GridFS ID
        "filename": filename,
        "status": "pending",
        "fields": [],
        "records_count": 0,
    }
    await db_manager.db.files.insert_one(file_doc)
    return file_doc


async def get_file_content_as_string(file_id: str) -> str:
    """Retrieves file bytes from GridFS and decodes to string."""
    try:
        oid = ObjectId(file_id)
        grid_out = await db_manager.fs_bucket.open_download_stream(oid)
        content = await grid_out.read()
        return content.decode("utf-8-sig")  # Handle BOM if present
    except Exception as e:
        raise ValueError(f"Could not read file from storage: {e}")


async def update_file_status(file_id: str, fields: list, count: int) -> None:
    """Updates the file processing status."""
    await db_manager.db.files.update_one(
        {"_id": ObjectId(file_id)},
        {"$set": {"status": "processed", "fields": fields, "records_count": count}},
    )


async def delete_file(file_id: str) -> bool:
    """Deletes metadata and GridFS chunks."""
    oid = ObjectId(file_id)
    result = await db_manager.db.files.delete_one({"_id": oid})

    if result.deleted_count == 0:
        return False

    await db_manager.fs_bucket.delete(oid)
    return True


async def save_file_to_gridfs(file: UploadFile) -> ObjectId:
    content = await file.read()

    # ... size validation ...

    # 1. ENCRYPT BEFORE SAVE
    encrypted_content = encrypt_data(content)

    # Write Encrypted bytes
    grid_in = db_manager.fs_bucket.open_upload_stream(file.filename)
    await grid_in.write(encrypted_content)  # Writing encrypted data
    await grid_in.close()

    return grid_in._id


async def get_file_content_as_string(file_id: str) -> str:
    try:
        oid = ObjectId(file_id)
        grid_out = await db_manager.fs_bucket.open_download_stream(oid)
        encrypted_content = await grid_out.read()

        # 2. DECRYPT AFTER READ
        decrypted_content = decrypt_data(encrypted_content)

        return decrypted_content.decode("utf-8-sig")
    except Exception as e:
        raise ValueError(f"Could not read/decrypt file: {e}")


async def create_file_metadata(file_id: ObjectId, filename: str) -> dict:
    """Creates the initial metadata document with timestamp."""
    file_doc = {
        "_id": file_id,
        "filename": filename,
        "status": "pending",
        "fields": [],
        "records_count": 0,
        # ISO format with timezone awareness is crucial for TTL comparison
        "created_at": datetime.now(timezone.utc),
    }
    await db_manager.db.files.insert_one(file_doc)
    return file_doc
