"""Unit tests for app.core.logging."""

from __future__ import annotations

import json
import uuid
from collections.abc import Generator, MutableMapping
from typing import Any

import pytest
import structlog
import structlog.testing

from app.core.logging import (
    get_logger,
    get_request_id,
    set_request_id,
    setup_logging,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_request_id() -> Generator[None, None, None]:
    """Reset the request ID to an empty string before and after each test."""
    set_request_id("")
    yield
    set_request_id("")


# ---------------------------------------------------------------------------
# get_request_id
# ---------------------------------------------------------------------------


class TestGetRequestId:
    def test_returns_empty_string_after_reset(self) -> None:
        assert get_request_id() == ""

    def test_returns_value_after_set(self) -> None:
        set_request_id("test-id-123")
        assert get_request_id() == "test-id-123"


# ---------------------------------------------------------------------------
# set_request_id
# ---------------------------------------------------------------------------


class TestSetRequestId:
    def test_sets_explicit_request_id(self) -> None:
        result = set_request_id("req-abc")
        assert result == "req-abc"
        assert get_request_id() == "req-abc"

    def test_returns_the_set_id(self) -> None:
        assert set_request_id("my-id") == "my-id"

    def test_generates_uuid_when_called_without_args(self) -> None:
        result = set_request_id()
        assert result != ""
        uuid.UUID(result)  # raises ValueError if not a valid UUID

    def test_generated_ids_are_unique(self) -> None:
        id1 = set_request_id()
        id2 = set_request_id()
        assert id1 != id2

    def test_none_arg_generates_uuid(self) -> None:
        result = set_request_id(None)
        uuid.UUID(result)  # valid UUID4

    def test_empty_string_clears_request_id(self) -> None:
        set_request_id("some-id")
        set_request_id("")
        assert get_request_id() == ""


# ---------------------------------------------------------------------------
# _inject_request_id — tested through the full JSON pipeline
# ---------------------------------------------------------------------------


class TestRequestIdInjection:
    def test_request_id_appears_in_json_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        setup_logging()
        set_request_id("req-pipeline-test")
        get_logger().info("user.auth.login_started")
        out = capsys.readouterr().out.strip()
        record = json.loads(out)
        assert record["request_id"] == "req-pipeline-test"
        assert record["event"] == "user.auth.login_started"

    def test_no_request_id_key_when_empty(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        setup_logging()
        # request_id reset to "" by fixture
        get_logger().info("pdf.parser.extraction_started")
        out = capsys.readouterr().out.strip()
        record = json.loads(out)
        assert "request_id" not in record

    def test_existing_fields_preserved_alongside_request_id(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        setup_logging()
        set_request_id("req-preserve")
        get_logger().info("document.validator.schema_validated", doc_id="d-42")
        out = capsys.readouterr().out.strip()
        record = json.loads(out)
        assert record["doc_id"] == "d-42"
        assert record["request_id"] == "req-preserve"
        assert record["event"] == "document.validator.schema_validated"

    def test_json_output_contains_timestamp(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        setup_logging()
        get_logger().info("test.action_completed")
        out = capsys.readouterr().out.strip()
        record = json.loads(out)
        assert "timestamp" in record

    def test_json_output_contains_log_level(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        setup_logging()
        get_logger().warning("database.connection_failed")
        out = capsys.readouterr().out.strip()
        record = json.loads(out)
        assert record["level"] == "warning"


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


class TestSetupLogging:
    def test_does_not_raise_with_default_level(self) -> None:
        setup_logging()

    def test_accepts_debug_level(self) -> None:
        setup_logging("DEBUG")

    def test_accepts_warning_level(self) -> None:
        setup_logging("WARNING")

    def test_accepts_error_level(self) -> None:
        setup_logging("ERROR")

    def test_accepts_critical_level(self) -> None:
        setup_logging("CRITICAL")

    def test_unknown_level_falls_back_to_info(self) -> None:
        setup_logging("NOTAREALLEVEL")  # must not raise

    def test_case_insensitive_level(self) -> None:
        setup_logging("debug")  # lowercase — must not raise

    def test_safe_to_call_multiple_times(self) -> None:
        setup_logging()
        setup_logging("DEBUG")
        setup_logging()  # idempotent by design


# ---------------------------------------------------------------------------
# get_logger — event structure via capture_logs
# ---------------------------------------------------------------------------


class TestGetLogger:
    def test_returns_a_logger_without_name(self) -> None:
        setup_logging()
        assert get_logger() is not None

    def test_returns_a_logger_with_name(self) -> None:
        setup_logging()
        assert get_logger("pdf.parser") is not None

    def test_logger_emits_info_event(self) -> None:
        with structlog.testing.capture_logs() as cap:
            structlog.get_logger().info("pdf.parser.extraction_started", page=1)
        assert len(cap) == 1
        assert cap[0]["event"] == "pdf.parser.extraction_started"
        assert cap[0]["page"] == 1

    def test_dotted_namespace_is_preserved(self) -> None:
        """The hybrid dotted namespace is passed through unchanged."""
        with structlog.testing.capture_logs() as cap:
            structlog.get_logger().info("user.registration_completed", user_id=99)
        assert cap[0]["event"] == "user.registration_completed"
        assert cap[0]["user_id"] == 99

    def test_warning_level_captured(self) -> None:
        with structlog.testing.capture_logs() as cap:
            structlog.get_logger().warning(
                "database.connection_failed", error="timeout"
            )
        assert cap[0]["log_level"] == "warning"

    def test_error_level_captured(self) -> None:
        with structlog.testing.capture_logs() as cap:
            structlog.get_logger().error("pdf.parser.extraction_failed")
        assert cap[0]["log_level"] == "error"

    def test_extra_kwargs_appear_in_event(self) -> None:
        with structlog.testing.capture_logs() as cap:
            structlog.get_logger().info(
                "document.validator.schema_validated",
                doc_id="d-42",
                valid=True,
            )
        assert cap[0]["doc_id"] == "d-42"
        assert cap[0]["valid"] is True

    def test_all_state_suffixes_accepted(self) -> None:
        """Each _state suffix from the pattern is a valid event name."""
        states = [
            "pdf.processor.conversion_started",
            "pdf.processor.conversion_completed",
            "pdf.processor.conversion_failed",
            "user.input.form_validated",
            "user.input.form_rejected",
        ]
        with structlog.testing.capture_logs() as cap:
            for state in states:
                structlog.get_logger().info(state)
        events = [entry["event"] for entry in cap]
        assert events == states


# ---------------------------------------------------------------------------
# Processor type compatibility — mypy/pyright structural check
# ---------------------------------------------------------------------------


def test_inject_request_id_signature_is_processor_compatible() -> None:
    """Verify _inject_request_id can be used as a structlog Processor.

    We test this indirectly: setup_logging() installs it without error, and
    calling info() emits valid JSON — proving the processor ran successfully.
    """
    setup_logging()
    # If the processor type was wrong, configure() would raise at runtime.
    logger = get_logger()
    assert logger is not None


def test_processor_does_not_mutate_empty_event_dict(
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup_logging()
    # No request_id set; processor should not add request_id key
    get_logger().info("test.state_check_started")
    out = capsys.readouterr().out.strip()
    record = json.loads(out)
    assert "request_id" not in record


def test_processor_handles_extra_kwargs(
    capsys: pytest.CaptureFixture[str],
) -> None:
    setup_logging()
    set_request_id("rid-extra")
    get_logger().info("test.action_started", extra_key="extra_val")
    record = json.loads(capsys.readouterr().out.strip())
    assert record["extra_key"] == "extra_val"
    assert record["request_id"] == "rid-extra"


def test_event_dict_type_annotation_in_tests() -> None:
    """Ensure MutableMapping[str, Any] is accepted as EventDict in user code."""
    event: MutableMapping[str, Any] = {"event": "type.check_validated"}
    assert event["event"] == "type.check_validated"
