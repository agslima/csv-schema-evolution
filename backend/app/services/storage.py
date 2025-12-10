"""
Module for handling file storage operations using GridFS and MongoDB.
Provides functionality to save, retrieve, and delete files.
"""

from bson import ObjectId

# Fix C0415: Import moved to top-level
from app.utils.validators import MAX_FILE_SIZE
from app.db.mongo import db, fs_bucket


async def save_file(file):
    """
    Save an uploaded file to GridFS and create a corresponding metadata document.

    Args:
        file: The file object to upload (must have filename and read method).

    Returns:
        ObjectId: The ID of the inserted metadata document.

    Raises:
        ValueError: If the file size exceeds the allowed limit.
    """
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File exceeds maximum size of 50MB")

    # Open upload stream to GridFS
    grid_in = fs_bucket.open_upload_stream(file.filename)
    grid_in.write(content)
    grid_in.close()

    # Save metadata to custom collection
    file_doc = {
        "filename": file.filename,
        "status": "pending",
        "size": len(content),
        "fields": [],
        "records_count": 0,
    }
    result = await db.files.insert_one(file_doc)
    return result.inserted_id


async def get_file_stream(file_id: str):
    """
    Retrieve a file stream and its metadata from GridFS.

    Args:
        file_id (str): The ID of the file to retrieve.

    Returns:
        tuple: (gridfs_stream, file_document) or None if not found.
    """
    doc = await db.files.find_one({"_id": ObjectId(file_id)})
    if not doc:
        return None
    cursor = fs_bucket.open_download_stream_by_name(doc["filename"])
    return cursor, doc


async def delete_file(file_id: str):
    """
    Delete a file from both the metadata collection and GridFS.

    Args:
        file_id (str): The ID of the file to delete.

    Returns:
        bool: True if file was found and deleted, False otherwise.
    """
    doc = await db.files.find_one({"_id": ObjectId(file_id)})
    if not doc:
        return False

    await db.files.delete_one({"_id": ObjectId(file_id)})

    # Delete from GridFS
    # Note: fs_bucket.find returns a cursor.
    cursor = fs_bucket.find({"filename": doc["filename"]})

    # Fixed C0103: Renamed 'f' to 'grid_file'
    for grid_file in cursor:
        # Fixed W0212: Suppress protected-access as _id is standard in Mongo
        # pylint: disable=protected-access
        fs_bucket.delete(grid_file._id)

    return True
