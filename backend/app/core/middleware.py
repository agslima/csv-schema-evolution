"""
Middleware for logging HTTP requests and adding Request IDs.
"""

import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from pythonjsonlogger import jsonlogger

# Configure JSON Logger
LOGGER = logging.getLogger("api_logger")
LOG_HANDLER = logging.StreamHandler()
FORMATTER = jsonlogger.JsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
LOG_HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(LOG_HANDLER)
LOGGER.setLevel(logging.INFO)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log request details (method, path, status, duration)
    and inject a unique X-Request-ID header.
    """

    # Middleware classes often only have the dispatch method
    # pylint: disable=too-few-public-methods

    async def dispatch(self, request: Request, call_next):
        """
        Intercepts the request, logs metadata, and adds a request ID.
        """
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Inject ID into request state for other services to use
        request.state.request_id = request_id

        # Process request
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000

            # Log Success
            LOGGER.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(process_time, 2),
                },
            )

            # Return custom header
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as error:
            # Log Exception
            LOGGER.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(error),
                },
            )
            raise error
