"""Financial PDF Converter — core typed utilities.

Fully-annotated module used to validate mypy strict + pyright strict
pass cleanly with no errors.
"""

import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


# ── Typed decorator using ParamSpec ──────────────────────────────────────────

def log_call(func: Callable[P, T]) -> Callable[P, T]:
    """Log the name of any function before calling it."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        print(f"→ {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


# ── Domain model ─────────────────────────────────────────────────────────────

def _empty_tags() -> list[str]:
    return []


@dataclass
class Document:
    """A PDF document with metadata."""

    name: str
    page_count: int
    tags: list[str] = field(default_factory=_empty_tags)
    file_path: str | None = None


# ── Pure typed functions ──────────────────────────────────────────────────────

def summarise(docs: list[Document]) -> dict[str, int]:
    """Return a name → page_count mapping."""
    return {doc.name: doc.page_count for doc in docs}


def find(name: str, docs: list[Document]) -> Document | None:
    """Return the first document matching *name*, or None."""
    return next((d for d in docs if d.name == name), None)


def page_count(name: str, docs: list[Document]) -> int:
    """Return the page count for *name*, or 0 if not found."""
    doc = find(name, docs)
    if doc is None:
        return 0
    return doc.page_count  # None branch already handled above


def filter_tagged(tag: str, docs: list[Document]) -> list[Document]:
    """Return all documents that carry *tag*."""
    return [d for d in docs if tag in d.tags]


def total_pages(docs: list[Document]) -> int:
    """Sum page counts across a collection."""
    return sum(d.page_count for d in docs)


# ── Entry point ───────────────────────────────────────────────────────────────

@log_call
def main() -> None:
    docs: list[Document] = [
        Document("invoice_001.pdf", 3, tags=["finance", "invoice"]),
        Document("statement_q1.pdf", 12, tags=["finance"], file_path="/reports/q1.pdf"),
        Document("contract_nda.pdf", 5, tags=["legal"]),
    ]

    summary: dict[str, int] = summarise(docs)
    for name, pages in summary.items():
        print(f"  {name}: {pages} pages")

    finance_docs: list[Document] = filter_tagged("finance", docs)
    print(f"Finance docs: {len(finance_docs)}, total pages: {total_pages(finance_docs)}")

    count: int = page_count("invoice_001.pdf", docs)
    print(f"invoice_001.pdf page count: {count}")


if __name__ == "__main__":
    main()
