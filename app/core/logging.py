"""Structured logging for FinancialPDFConverter.

JSON output, request-ID correlation, and the hybrid dotted namespace pattern::

    {domain}.{component}.{action}_{state}

States: ``_started``, ``_completed``, ``_failed``, ``_validated``, ``_rejected``

Examples::

    logger.info("pdf.parser.extraction_started", document="invoice.pdf")
    logger.info("user.auth.login_completed", user_id=42)
    logger.error("database.connection.init_failed", exc_info=True)
"""

from __future__ import annotations

import contextvars
import logging
import uuid
from typing import Any, cast

import structlog
from structlog.typing import EventDict, FilteringBoundLogger

# ---------------------------------------------------------------------------
# Request-ID context variable — propagates through async call chains
# ---------------------------------------------------------------------------

_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


def get_request_id() -> str:
    """Return the active request ID, or ``""`` when none is set."""
    return _request_id_var.get()


def set_request_id(request_id: str | None = None) -> str:
    """Bind a request ID to the current context.

    Generates a UUID4 automatically when *request_id* is omitted or ``None``.
    Returns the ID that was set.
    """
    rid = request_id if request_id is not None else str(uuid.uuid4())
    _request_id_var.set(rid)
    return rid


# ---------------------------------------------------------------------------
# Custom structlog processor
# ---------------------------------------------------------------------------


def _inject_request_id(
    _logger: object,
    _method: str,
    event_dict: EventDict,
) -> EventDict:
    """Structlog processor: attach *request_id* from the context variable."""
    rid = _request_id_var.get()
    if rid:
        event_dict["request_id"] = rid
    return event_dict


# ---------------------------------------------------------------------------
# Log-level lookup — avoids the ambiguous str | int from getLevelName
# ---------------------------------------------------------------------------

_LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog for JSON output with request-ID correlation.

    Call once at application startup before the first log is emitted.
    Safe to call multiple times (e.g. in tests) because
    ``cache_logger_on_first_use=False`` is set.
    """
    level = _LEVEL_MAP.get(log_level.upper(), logging.INFO)

    processors: list[Any] = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _inject_request_id,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    """Return a structlog logger, optionally bound to *name*.

    Example::

        logger = get_logger(__name__)
        logger.info("pdf.processor.conversion_started", document="invoice.pdf")
    """
    raw: Any = (
        structlog.get_logger(name) if name is not None else structlog.get_logger()
    )
    return cast(FilteringBoundLogger, raw)
