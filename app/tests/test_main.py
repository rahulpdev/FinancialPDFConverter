"""Integration tests for app.main (FastAPI application)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import structlog.testing
from fastapi.testclient import TestClient

from app.core.logging import setup_logging
from app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def configure_logging() -> None:
    setup_logging()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------


class TestRootEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200

    def test_returns_correct_json_structure(self, client: TestClient) -> None:
        response = client.get("/")
        body = response.json()
        assert "message" in body
        assert "version" in body
        assert "docs" in body

    def test_docs_points_to_correct_path(self, client: TestClient) -> None:
        body = client.get("/").json()
        assert body["docs"] == "/docs"

    def test_version_is_semver_like(self, client: TestClient) -> None:
        body = client.get("/").json()
        parts = body["version"].split(".")
        assert len(parts) == 3


# ---------------------------------------------------------------------------
# Docs endpoint
# ---------------------------------------------------------------------------


class TestDocsEndpoint:
    def test_swagger_ui_is_accessible(self, client: TestClient) -> None:
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_is_accessible(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Middleware integration
# ---------------------------------------------------------------------------


class TestCORSHeaders:
    def test_cors_header_present_for_allowed_origin(self, client: TestClient) -> None:
        response = client.get(
            "/", headers={"Origin": "http://localhost:3000"}
        )
        assert "access-control-allow-origin" in response.headers

    def test_request_id_header_in_response(self, client: TestClient) -> None:
        response = client.get("/")
        assert "X-Request-ID" in response.headers


# ---------------------------------------------------------------------------
# Lifespan / startup logging
# ---------------------------------------------------------------------------


class TestLifespanLogging:
    def test_startup_log_emitted(self) -> None:
        # patch enters before capture_logs so setup_logging doesn't override it.
        with patch("app.main.setup_logging"), structlog.testing.capture_logs() as logs, TestClient(app):
            pass
        events = [e["event"] for e in logs]
        assert "application.startup" in events

    def test_shutdown_log_emitted(self) -> None:
        with patch("app.main.setup_logging"), structlog.testing.capture_logs() as logs, TestClient(app):
            pass
        events = [e["event"] for e in logs]
        assert "application.shutdown" in events
