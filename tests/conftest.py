"""Shared pytest fixtures for FinancialPDFConverter tests."""

import pytest

from main import Document, fetch_document


@pytest.fixture
def sample_docs() -> list[Document]:
    """A standard collection of three documents for sync tests."""
    return [
        Document("invoice_001.pdf", 3, tags=["finance", "invoice"]),
        Document("statement_q1.pdf", 12, tags=["finance"]),
        Document("contract_nda.pdf", 5, tags=["legal"]),
    ]


@pytest.fixture
async def fetched_invoice() -> Document:
    """Async fixture: resolves a Document via fetch_document."""
    doc = await fetch_document("/data/invoice_001.pdf")
    assert doc is not None, "fetch_document must return a Document for a .pdf path"
    return doc
