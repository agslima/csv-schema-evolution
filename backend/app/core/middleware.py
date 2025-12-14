"""
Middleware for logging HTTP requests and adding Request IDs.
"""

import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# We just ask for a logger. We TRUST logging.py has configured it correctly.
LOGGER = logging.getLogger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log request details (method, path, status, duration)
    and inject a unique X-Request-ID header.
    """

    # pylint: disable=too-few-public-methods

    async def dispatch(self, request: Request, call_next):
        """
        Intercepts the request, logs metadata, and adds a request ID.
        """
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Inject ID into request state so other parts of the app can see it
        request.state.request_id = request_id

        # Context filter for logs (optional, strictly speaking) but helpful
        # Note: In a real async environment, we might use contextvars for this.

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000

            # Log Success - Notice we don't need to format it manually anymore
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

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as error:
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
