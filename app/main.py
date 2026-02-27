"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import setup_middleware


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level)

    logger = get_logger(__name__)
    logger.info("application.startup", environment=settings.environment)

    yield

    logger.info("application.shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        lifespan=lifespan,
    )

    setup_middleware(app)

    @app.get("/")
    async def root() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        return {
            "message": settings.app_name,
            "version": settings.version,
            "docs": "/docs",
        }

    return app


app = create_app()

if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8123, reload=True)
