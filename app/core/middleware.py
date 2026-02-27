"""HTTP middleware for the FastAPI application.

Provides:
- :class:`RequestLoggingMiddleware` — structured JSON logs per request,
  with request-ID propagation via the ``X-Request-ID`` header.
- :func:`setup_middleware` — one-call registration of all middleware.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.logging import get_logger, set_request_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request/response with a correlated request ID."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Use header value if provided, otherwise generate a new UUID.
        request_id = set_request_id(request.headers.get("X-Request-ID"))

        logger = get_logger(__name__)
        logger.info(
            "request.started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )

        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.error(
                "request.failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                exc_info=True,
            )
            raise

        duration = time.perf_counter() - started_at
        logger.info(
            "request.completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=round(duration, 6),
        )

        response.headers["X-Request-ID"] = request_id
        return response


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on *app* in the correct order.

    Middleware is applied in reverse-registration order by Starlette, so CORS
    is added last here so it executes first (outermost layer).
    """
    settings = get_settings()

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
