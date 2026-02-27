"""Unit tests for app.core.middleware."""

from __future__ import annotations

from collections.abc import Generator

import pytest
import structlog.testing
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.logging import set_request_id, setup_logging
from app.core.middleware import setup_middleware

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_request_id() -> Generator[None, None, None]:
    """Ensure request ID is clean before and after each test."""
    set_request_id("")
    yield
    set_request_id("")


@pytest.fixture()
def app_with_middleware() -> FastAPI:
    """Minimal FastAPI app with all middleware registered."""
    app = FastAPI()
    setup_middleware(app)

    @app.get("/ok")
    async def ok() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        return {"status": "ok"}

    @app.get("/fail")
    async def fail() -> None:  # pyright: ignore[reportUnusedFunction]
        raise RuntimeError("boom")

    return app


@pytest.fixture()
def client(app_with_middleware: FastAPI) -> TestClient:
    setup_logging()
    return TestClient(app_with_middleware, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRequestIdGeneration:
    def test_generates_request_id_when_header_absent(self, client: TestClient) -> None:
        with structlog.testing.capture_logs() as logs:
            client.get("/ok")
        started = next(e for e in logs if e["event"] == "request.started")
        assert "request_id" in started
        assert started["request_id"] != ""

    def test_uses_x_request_id_header_when_provided(self, client: TestClient) -> None:
        with structlog.testing.capture_logs() as logs:
            client.get("/ok", headers={"X-Request-ID": "custom-id-abc"})
        started = next(e for e in logs if e["event"] == "request.started")
        assert started["request_id"] == "custom-id-abc"

    def test_x_request_id_echoed_in_response_headers(self, client: TestClient) -> None:
        response = client.get("/ok", headers={"X-Request-ID": "echo-me"})
        assert response.headers["X-Request-ID"] == "echo-me"

    def test_generated_request_id_in_response_headers(self, client: TestClient) -> None:
        response = client.get("/ok")
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] != ""


class TestRequestLogging:
    def test_logs_request_started(self, client: TestClient) -> None:
        with structlog.testing.capture_logs() as logs:
            client.get("/ok")
        events = [e["event"] for e in logs]
        assert "request.started" in events

    def test_logs_request_completed(self, client: TestClient) -> None:
        with structlog.testing.capture_logs() as logs:
            client.get("/ok")
        events = [e["event"] for e in logs]
        assert "request.completed" in events

    def test_completed_log_includes_status_code(self, client: TestClient) -> None:
        with structlog.testing.capture_logs() as logs:
            client.get("/ok")
        completed = next(e for e in logs if e["event"] == "request.completed")
        assert completed["status_code"] == 200

    def test_completed_log_includes_duration(self, client: TestClient) -> None:
        with structlog.testing.capture_logs() as logs:
            client.get("/ok")
        completed = next(e for e in logs if e["event"] == "request.completed")
        assert "duration_seconds" in completed
        assert isinstance(completed["duration_seconds"], float)

    def test_logs_request_failed_on_exception(self, client: TestClient) -> None:
        with structlog.testing.capture_logs() as logs:
            client.get("/fail")
        events = [e["event"] for e in logs]
        assert "request.failed" in events
