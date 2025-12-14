"""
Module for handling file storage operations using GridFS and MongoDB.
Provides functionality to save, retrieve, and delete files.
"""

from datetime import datetime, timezone
from bson import ObjectId
from fastapi import UploadFile
from app.db.mongo import db_manager
from app.core.config import settings
from app.core.security import encrypt_data, decrypt_data


async def save_bytes_to_gridfs(content: bytes, filename: str) -> ObjectId:
    """
    Saves raw bytes (already sanitized) to GridFS with encryption.

    Args:
        content: The raw file content in bytes.
        filename: The name of the file to save.

    Returns:
        ObjectId: The ID of the saved file in GridFS.

    Raises:
        ValueError: If file size exceeds the configured limit.
    """
    if len(content) > settings.max_file_size_bytes:
        raise ValueError(f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB")

    # Encrypt content before storage
    encrypted_content = encrypt_data(content)

    # Open upload stream
    grid_in = db_manager.fs_bucket.open_upload_stream(filename)
    await grid_in.write(encrypted_content)
    await grid_in.close()

    # pylint: disable=protected-access
    return grid_in._id


async def save_file_to_gridfs(file: UploadFile) -> ObjectId:
    """
    Reads the file stream, encrypts it, and saves it to MongoDB GridFS.
    (Kept for backward compatibility or raw uploads if needed later)

    Raises:
        ValueError: If file size exceeds the configured limit.
    """
    content = await file.read()
    # Delegate to the bytes saver to avoid logic duplication
    return await save_bytes_to_gridfs(content, file.filename)


async def create_file_metadata(file_id: ObjectId, filename: str) -> dict:
    """Creates the initial metadata document in the 'files' collection."""
    file_doc = {
        "_id": file_id,  # Link directly to GridFS ID
        "filename": filename,
        "status": "pending",
        "fields": [],
        "records_count": 0,
        # ISO format with timezone awareness is crucial for TTL comparison
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

        # Decrypt after reading
        decrypted_content = decrypt_data(encrypted_content)

        return decrypted_content.decode("utf-8-sig")  # Handle BOM if present
    except Exception as e:
        raise ValueError(f"Could not read/decrypt file from storage: {e}") from e


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
