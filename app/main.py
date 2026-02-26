"""Example: structured logging with the hybrid dotted namespace pattern.

Pattern: {domain}.{component}.{action}_{state}

States: _started, _completed, _failed, _validated, _rejected
"""

from app.core.logging import get_logger, set_request_id, setup_logging


def process_document(doc_name: str) -> None:
    """Convert a PDF document with structured log events at each step."""
    logger = get_logger(__name__)
    logger.info("pdf.processor.conversion_started", document=doc_name)
    try:
        # Simulate processing
        pages = 10
        logger.info(
            "pdf.processor.conversion_completed",
            document=doc_name,
            pages=pages,
        )
    except Exception:
        logger.exception(
            "pdf.processor.conversion_failed",
            document=doc_name,
        )


def main() -> None:
    """Demonstrate structured logging with request-ID correlation."""
    setup_logging()
    request_id = set_request_id()

    logger = get_logger(__name__)
    logger.info("app.lifecycle.startup_started", request_id=request_id)

    process_document("invoice_001.pdf")
    process_document("statement_q1.pdf")

    logger.info("app.lifecycle.startup_completed")


if __name__ == "__main__":
    main()  # pragma: no cover
