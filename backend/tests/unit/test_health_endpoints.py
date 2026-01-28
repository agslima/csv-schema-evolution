"""
Unit tests for health API endpoints.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Response, status

from app.api.v1.endpoints.health import health_check, liveness_check, readiness_check
from app.db.mongo import db_manager


@pytest.mark.asyncio
async def test_health_and_liveness_checks_return_ok():
    assert await health_check() == {"status": "ok"}
    assert await liveness_check() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness_check_db_and_gridfs_not_initialized(monkeypatch):
    monkeypatch.setattr(db_manager, "db", None)
    monkeypatch.setattr(db_manager, "fs_bucket", None)

    response = Response()
    payload = await readiness_check(response)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert payload["status"] == "error"
    assert payload["dependencies"]["mongo"]["detail"] == "not initialized"
    assert payload["dependencies"]["gridfs"]["detail"] == "not initialized"


@pytest.mark.asyncio
async def test_readiness_check_mongo_ping_failure_marks_gridfs_unavailable(
    monkeypatch,
):
    mock_db = MagicMock()
    mock_db.command = AsyncMock(side_effect=Exception("ping failed"))

    mock_fs = MagicMock()
    mock_fs.bucket_name = "fs"

    monkeypatch.setattr(db_manager, "db", mock_db)
    monkeypatch.setattr(db_manager, "fs_bucket", mock_fs)

    response = Response()
    payload = await readiness_check(response)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert payload["dependencies"]["mongo"]["status"] == "error"
    assert "ping failed" in payload["dependencies"]["mongo"]["detail"]
    assert payload["dependencies"]["gridfs"]["detail"] == "mongo unavailable"


@pytest.mark.asyncio
async def test_readiness_check_gridfs_query_failure(monkeypatch):
    mock_db = MagicMock()
    mock_db.command = AsyncMock(return_value={"ok": 1})

    mock_gridfs_files = MagicMock()
    mock_gridfs_files.find_one = AsyncMock(side_effect=Exception("gridfs down"))
    mock_db.__getitem__.return_value = mock_gridfs_files

    mock_fs = MagicMock()
    mock_fs.bucket_name = "fs"

    monkeypatch.setattr(db_manager, "db", mock_db)
    monkeypatch.setattr(db_manager, "fs_bucket", mock_fs)

    response = Response()
    payload = await readiness_check(response)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert payload["dependencies"]["mongo"]["status"] == "ok"
    assert payload["dependencies"]["gridfs"]["status"] == "error"
    assert "gridfs down" in payload["dependencies"]["gridfs"]["detail"]


@pytest.mark.asyncio
async def test_readiness_check_ok(monkeypatch):
    mock_db = MagicMock()
    mock_db.command = AsyncMock(return_value={"ok": 1})

    mock_gridfs_files = MagicMock()
    mock_gridfs_files.find_one = AsyncMock(return_value={"_id": "x"})
    mock_db.__getitem__.return_value = mock_gridfs_files

    mock_fs = MagicMock()
    mock_fs.bucket_name = "fs"

    monkeypatch.setattr(db_manager, "db", mock_db)
    monkeypatch.setattr(db_manager, "fs_bucket", mock_fs)

    response = Response()
    payload = await readiness_check(response)

    assert response.status_code == status.HTTP_200_OK
    assert payload["status"] == "ok"
    assert payload["dependencies"]["mongo"]["status"] == "ok"
    assert payload["dependencies"]["gridfs"]["status"] == "ok"
    assert payload["dependencies"]["gridfs"]["bucket"] == "fs"
