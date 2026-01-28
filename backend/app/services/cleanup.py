"""
Background cleanup service for expired files.
"""

import logging
from datetime import datetime, timedelta, timezone
from app.db.mongo import db_manager
from app.repositories import file_repository

logger = logging.getLogger(__name__)

# Configuration: Files older than 24 hours are deleted
RETENTION_PERIOD_HOURS = 24


async def delete_expired_files():
    """
    Background Task: Finds and removes files exceeding the retention period.
    Ensures LGPD Data Minimization compliance by permanently removing old data.
    """
    try:
        # Calculate the cutoff time (Now - 24h)
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            hours=RETENTION_PERIOD_HOURS
        )

        logger.info(
            "Running scheduled cleanup. Looking for files created before %s",
            cutoff_time,
        )

        # Find files where 'created_at' is less than (older than) cutoff_time
        cursor = db_manager.db.files.find({"created_at": {"$lt": cutoff_time}})

        deleted_count = 0
        async for doc in cursor:
            file_id = str(doc["_id"])
            try:
                # Reuse our robust delete logic (which handles GridFS + Metadata)
                await file_repository.delete_file(file_id)
                deleted_count += 1
                logger.info("Auto-deleted expired file: %s", file_id)
            # pylint: disable=broad-except
            except Exception as err:
                logger.error("Failed to auto-delete file %s: %s", file_id, err)

        if deleted_count > 0:
            logger.info("Cleanup complete. Removed %d expired files.", deleted_count)
        else:
            logger.info("Cleanup complete. No expired files found.")

    # pylint: disable=broad-except
    except Exception as err:
        logger.error("Error during scheduled cleanup: %s", err)
