"""
Logging Configuration.
Sets up structured JSON logging for the entire application.
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def setup_logging():
    """
    Configures the root logger to use JSON formatting.
    """
    logger = logging.getLogger()

    # Set global log level
    logger.setLevel(settings.LOG_LEVEL)

    # Clear existing handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create Handler (Output to Console)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.LOG_LEVEL)

    # --- FIX: REMOVED rename_fields TO PREVENT KeyError ---
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # -------------------------------------------------------

    handler.setFormatter(formatter)

    # Add handler to root logger
    logger.addHandler(handler)

    # Silence noisy libraries
    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(
        logging.WARNING
    )  # Optional: Silence scheduler noise
