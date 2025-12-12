import time
import uuid
import logging
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from pythonjsonlogger import jsonlogger

# Configure JSON Logger
logger = logging.getLogger("api_logger")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Inject ID into request state for other services to use
        request.state.request_id = request_id

        # Process request
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000

            # Log Success
            logger.info(
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

        except Exception as e:
            # Log Exception
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
            )
            raise e
