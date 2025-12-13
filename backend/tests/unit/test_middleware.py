"""
Unit tests for the Request Log Middleware.
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.core.middleware import RequestLogMiddleware


@pytest.mark.asyncio
async def test_request_id_middleware():
    """
    Creates a temporary app just to test if the Middleware
    injects the X-Request-ID header and processes the request.
    """
    # 1. Setup Minimal App
    app = FastAPI()
    app.add_middleware(RequestLogMiddleware)

    @app.get("/ping")
    async def ping():
        return {"msg": "pong"}

    # 2. Execute Request
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/ping")

    # 3. Asserts
    assert response.status_code == 200
    assert response.json() == {"msg": "pong"}

    # Verify if header was injected
    assert "X-Request-ID" in response.headers
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) > 0
