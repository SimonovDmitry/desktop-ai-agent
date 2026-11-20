from types import SimpleNamespace
import sys

from deskagent.actions.documents.reading import (
    CompareDocumentVersions,
    GetDocumentSummary,
    ReadPDFPages,
    SearchInDocument,
)


def test_text_document_search_summary_and_comparison(tmp_path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("A detailed first sentence about the original project.\nSecond line.", encoding="utf-8")
    second.write_text("A detailed first sentence about the revised project.\nSecond line.", encoding="utf-8")
    context = SimpleNamespace()
    search = SearchInDocument().execute(context, {"path": str(first), "query": "original"})
    summary = GetDocumentSummary().execute(context, {"path": str(first)})
    comparison = CompareDocumentVersions().execute(context, {"source": str(first), "destination": str(second)})
    assert search.success and search.data["matches"][0]["page"] == 1
    assert summary.success and summary.data["method"] == "extractive"
    assert comparison.success and comparison.data["changed"]


def test_read_pdf_pages_keeps_page_numbers(tmp_path, monkeypatch):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"%PDF-1.7")

    class Reader:
        def __init__(self, source):
            self.pages = [SimpleNamespace(extract_text=lambda value=value: value) for value in ("one", "two", "three")]

    monkeypatch.setitem(sys.modules, "pypdf", SimpleNamespace(PdfReader=Reader))
    result = ReadPDFPages().execute(None, {"path": str(pdf), "start_page": 2, "page_count": 1})
    assert result.success
    assert result.data["pages"] == [{"page": 2, "text": "two"}]
