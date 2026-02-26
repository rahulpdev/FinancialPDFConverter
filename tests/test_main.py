"""Tests for main.py — covers sync functions and async fetch_document."""

import pytest

from main import (
    Document,
    fetch_document,
    filter_tagged,
    find,
    log_call,
    main,
    page_count,
    summarise,
    total_pages,
)

# ── Document dataclass ────────────────────────────────────────────────────────


class TestDocument:
    def test_default_tags_are_empty(self) -> None:
        doc = Document("test.pdf", 1)
        assert doc.tags == []

    def test_file_path_defaults_to_none(self) -> None:
        doc = Document("test.pdf", 1)
        assert doc.file_path is None

    def test_tags_are_independent_per_instance(self) -> None:
        """Verifies _empty_tags() returns a new list each time."""
        doc1 = Document("a.pdf", 1)
        doc2 = Document("b.pdf", 2)
        doc1.tags.append("finance")
        assert doc2.tags == []


# ── summarise ─────────────────────────────────────────────────────────────────


class TestSummarise:
    def test_maps_names_to_page_counts(self, sample_docs: list[Document]) -> None:
        assert summarise(sample_docs) == {
            "invoice_001.pdf": 3,
            "statement_q1.pdf": 12,
            "contract_nda.pdf": 5,
        }

    def test_empty_input_returns_empty_dict(self) -> None:
        assert summarise([]) == {}


# ── find ──────────────────────────────────────────────────────────────────────


class TestFind:
    def test_returns_matching_document(self, sample_docs: list[Document]) -> None:
        doc = find("invoice_001.pdf", sample_docs)
        assert doc is not None
        assert doc.page_count == 3

    def test_returns_none_when_not_found(self, sample_docs: list[Document]) -> None:
        assert find("missing.pdf", sample_docs) is None


# ── page_count ────────────────────────────────────────────────────────────────


class TestPageCount:
    def test_returns_page_count_for_existing_doc(
        self, sample_docs: list[Document]
    ) -> None:
        assert page_count("statement_q1.pdf", sample_docs) == 12

    def test_returns_zero_for_missing_doc(self, sample_docs: list[Document]) -> None:
        assert page_count("missing.pdf", sample_docs) == 0


# ── filter_tagged ─────────────────────────────────────────────────────────────


class TestFilterTagged:
    def test_returns_only_docs_with_tag(self, sample_docs: list[Document]) -> None:
        result = filter_tagged("finance", sample_docs)
        assert len(result) == 2
        assert all("finance" in d.tags for d in result)

    def test_returns_empty_when_no_match(self, sample_docs: list[Document]) -> None:
        assert filter_tagged("nonexistent", sample_docs) == []

    def test_single_document_match(self, sample_docs: list[Document]) -> None:
        result = filter_tagged("legal", sample_docs)
        assert len(result) == 1
        assert result[0].name == "contract_nda.pdf"


# ── total_pages ───────────────────────────────────────────────────────────────


class TestTotalPages:
    def test_sums_all_page_counts(self, sample_docs: list[Document]) -> None:
        assert total_pages(sample_docs) == 20  # 3 + 12 + 5

    def test_empty_collection_returns_zero(self) -> None:
        assert total_pages([]) == 0


# ── log_call decorator ───────────────────────────────────────────────────────


class TestLogCall:
    def test_prints_function_name(self, capsys: pytest.CaptureFixture[str]) -> None:
        @log_call
        def sample() -> int:
            return 42

        sample()
        assert "→ sample" in capsys.readouterr().out

    def test_preserves_return_value(self) -> None:
        @log_call
        def add(x: int, y: int) -> int:
            return x + y

        assert add(2, 3) == 5

    def test_preserves_function_name(self) -> None:
        @log_call
        def named_fn() -> None:
            pass

        assert named_fn.__name__ == "named_fn"


# ── main() ────────────────────────────────────────────────────────────────────


class TestMain:
    def test_runs_without_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        main()
        out = capsys.readouterr().out
        assert "invoice_001.pdf" in out
        assert "statement_q1.pdf" in out
        assert "contract_nda.pdf" in out

    def test_prints_finance_summary(self, capsys: pytest.CaptureFixture[str]) -> None:
        main()
        assert "Finance docs: 2" in capsys.readouterr().out

    def test_prints_invoice_page_count(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main()
        assert "invoice_001.pdf page count: 3" in capsys.readouterr().out


# ── fetch_document (async) ────────────────────────────────────────────────────


async def test_fetch_pdf_returns_document() -> None:
    doc = await fetch_document("/data/invoice.pdf")
    assert doc is not None
    assert doc.name == "invoice.pdf"
    assert doc.file_path == "/data/invoice.pdf"


async def test_fetch_non_pdf_returns_none() -> None:
    result = await fetch_document("/data/spreadsheet.xlsx")
    assert result is None


async def test_fetch_preserves_full_file_path() -> None:
    path = "/storage/reports/q1.pdf"
    doc = await fetch_document(path)
    assert doc is not None
    assert doc.file_path == path


async def test_fetch_extracts_filename_from_path() -> None:
    doc = await fetch_document("/deeply/nested/path/report.pdf")
    assert doc is not None
    assert doc.name == "report.pdf"


async def test_fetch_initialises_page_count_to_zero() -> None:
    doc = await fetch_document("/data/new.pdf")
    assert doc is not None
    assert doc.page_count == 0


async def test_async_fixture_resolves(fetched_invoice: Document) -> None:
    """Verify the async conftest fixture injects a resolved Document."""
    assert fetched_invoice.name == "invoice_001.pdf"
    assert fetched_invoice.file_path == "/data/invoice_001.pdf"


async def test_sequential_fetches_all_succeed() -> None:
    paths = ["/data/a.pdf", "/data/b.pdf", "/data/c.pdf"]
    docs = [await fetch_document(p) for p in paths]
    assert all(d is not None for d in docs)
    assert len(docs) == 3
