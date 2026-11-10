import sys
from pathlib import Path
from types import SimpleNamespace

from deskagent.actions.documents.pdf_edit import (
    ExportPdfText, ExtractPdfPages, MergePdfFiles, RemovePdfPages,
    ReorderPdfPages, RotatePdfPages, SetPdfMetadata,
)
from deskagent.actions.documents.pdf_inspection import (
    CheckPdfAccessibilityBasics, GetPdfAnnotations, GetPdfFormFields,
    GetPdfImageInventory, GetPdfLinks, GetPdfMetadata, GetPdfOutline,
    GetPdfPageDimensions, GetPdfPageTextStatistics,
)
from deskagent.actions.documents.text_analysis import (
    EstimateDocumentReadingTime, FindDuplicateParagraphs, GetDocumentHeadings,
    GetDocumentLinks, GetDocumentParagraphs, GetDocumentWordFrequencies,
    GetMarkdownTasks, InspectTextDocument, ReadTextLines,
)
from deskagent.actions.documents.text_edit import (
    AppendTextToDocument, CreateTextDocument, ExtractTextLines,
    JoinTextDocuments, NormalizeTextWhitespace, ReplaceTextInDocument,
)
from deskagent.actions.registry import create_action_registry
from deskagent.core.config import SecuritySettings, Settings


def context(tmp_path):
    return SimpleNamespace(settings=Settings(
        security=SecuritySettings(allowed_paths=[str(tmp_path)], blocked_paths=[])
    ))


def test_text_inspection_and_structure(tmp_path):
    source = tmp_path / "sample.md"
    source.write_text("# Title\n\nAlpha beta alpha. [Site](https://example.com)\n\n"
                      "- [x] Done\n- [ ] Pending\n\nAlpha beta alpha. [Site](https://example.com)\n",
                      encoding="utf-8")
    ctx = context(tmp_path)
    path = str(source)
    assert InspectTextDocument().execute(ctx, {"path": path}).data["paragraphs"] == 4
    assert ReadTextLines().execute(ctx, {"path": path, "start_line": 1, "line_count": 2}).data["lines"][0]["text"] == "# Title"
    assert GetDocumentHeadings().execute(ctx, {"path": path}).data["headings"][0]["title"] == "Title"
    assert len(GetDocumentParagraphs().execute(ctx, {"path": path}).data["paragraphs"]) == 4
    assert GetDocumentWordFrequencies().execute(ctx, {"path": path}).data["words"][0]["word"] == "alpha"
    assert FindDuplicateParagraphs().execute(ctx, {"path": path, "min_characters": 10}).data["total"] == 1
    assert GetDocumentLinks().execute(ctx, {"path": path}).data["total"] == 2
    assert GetMarkdownTasks().execute(ctx, {"path": path}).data["completed"] == 1
    assert EstimateDocumentReadingTime().execute(ctx, {"path": path}).data["words"] > 0


def test_text_writes_create_new_files_and_preserve_source(tmp_path):
    ctx = context(tmp_path)
    created = CreateTextDocument().execute(ctx, {
        "output_path": str(tmp_path / "created.txt"), "text": "A  \r\nB\n",
    })
    assert created.success
    source = Path(created.data["path"])
    normalized = NormalizeTextWhitespace().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "normalized.txt"),
    })
    replaced = ReplaceTextInDocument().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "replaced.txt"),
        "find": "A", "replace": "C",
    })
    appended = AppendTextToDocument().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "appended.txt"), "text": "END",
    })
    joined = JoinTextDocuments().execute(ctx, {
        "paths": [str(source), str(source)], "output_path": str(tmp_path / "joined.txt"),
    })
    extracted = ExtractTextLines().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path / "extracted.txt"),
        "start_line": 2, "end_line": 2,
    })
    assert all(item.success for item in (normalized, replaced, appended, joined, extracted))
    assert source.read_bytes() == b"A  \r\nB\n"
    assert (tmp_path / "normalized.txt").read_text() == "A\nB\n"
    assert (tmp_path / "replaced.txt").read_text().startswith("C")
    assert (tmp_path / "appended.txt").read_text().endswith("END")
    assert joined.data["sources"] == 2
    assert (tmp_path / "extracted.txt").read_text() == "B\n"
    collision = CreateTextDocument().execute(ctx, {"output_path": str(source), "text": "overwrite"})
    outside = CreateTextDocument().execute(ctx, {
        "output_path": str(tmp_path.parent / "outside.txt"), "text": "outside",
    })
    assert not collision.success and not outside.success
    assert source.read_bytes() == b"A  \r\nB\n"


class FakePage(dict):
    def __init__(self, number):
        super().__init__()
        self.number = number
        self.mediabox = SimpleNamespace(width=612, height=792)
        self.images = [SimpleNamespace(name="image.png", data=b"pixels")]
        self["/Annots"] = [SimpleNamespace(get_object=lambda: {
            "/Subtype": "/Link", "/A": {"/URI": "https://example.com"},
            "/Rect": [0, 0, 10, 10], "/T": "Reviewer", "/Contents": "Link",
        })]

    def extract_text(self):
        return f"Page {self.number} text"

    def rotate(self, degrees):
        self["/Rotate"] = degrees
        return self


class FakeReader:
    def __init__(self, path):
        self.pages = [FakePage(1), FakePage(2), FakePage(3)]
        self.metadata = {"/Title": "Sample"}
        self.is_encrypted = False
        self.trailer = {"/Root": {"/Lang": "en", "/MarkInfo": {"/Marked": True}}}
        self.outline = [SimpleNamespace(title="Introduction")]

    def get_destination_page_number(self, item):
        return 0

    def get_fields(self):
        return {"Name": {"/FT": "/Tx", "/V": "Alice"}}


class FakeWriter:
    def __init__(self):
        self.pages = []
        self.metadata = {}

    def add_page(self, page):
        self.pages.append(FakePage(page.number))

    def add_metadata(self, values):
        self.metadata.update(values)

    def write(self, path):
        Path(path).write_bytes(("%PDF-FAKE " + ",".join(str(page.number) for page in self.pages)).encode())


def test_pdf_read_and_write_actions_with_reader_contract(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "pypdf", SimpleNamespace(PdfReader=FakeReader, PdfWriter=FakeWriter))
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF-FAKE")
    ctx = context(tmp_path)
    path = str(source)
    assert GetPdfMetadata().execute(ctx, {"path": path}).data["page_count"] == 3
    assert GetPdfPageDimensions().execute(ctx, {"path": path, "page_count": 2}).data["pages"][0]["width_points"] == 612
    assert GetPdfPageTextStatistics().execute(ctx, {"path": path}).data["pages"][0]["words"] == 3
    assert CheckPdfAccessibilityBasics().execute(ctx, {"path": path}).data["tagged"]
    assert GetPdfOutline().execute(ctx, {"path": path}).data["bookmarks"][0]["page"] == 1
    assert GetPdfLinks().execute(ctx, {"path": path}).data["links"][0]["uri"] == "https://example.com"
    assert GetPdfAnnotations().execute(ctx, {"path": path}).data["annotations"][0]["author"] == "Reviewer"
    assert GetPdfFormFields().execute(ctx, {"path": path}).data["fields"][0]["value"] == "Alice"
    assert GetPdfImageInventory().execute(ctx, {"path": path}).data["images"][0]["bytes"] == 6
    actions = [
        (MergePdfFiles(), {"paths": [path, path], "output_path": str(tmp_path / "merged.pdf")}),
        (ExtractPdfPages(), {"path": path, "output_path": str(tmp_path / "extract.pdf"),
                             "start_page": 2, "page_count": 1}),
        (RemovePdfPages(), {"path": path, "output_path": str(tmp_path / "removed.pdf"), "pages": [2]}),
        (ReorderPdfPages(), {"path": path, "output_path": str(tmp_path / "reordered.pdf"),
                             "page_order": [3, 2, 1]}),
        (RotatePdfPages(), {"path": path, "output_path": str(tmp_path / "rotated.pdf"),
                            "pages": [2], "degrees": 90}),
        (SetPdfMetadata(), {"path": path, "output_path": str(tmp_path / "metadata.pdf"),
                            "title": "New"}),
        (ExportPdfText(), {"path": path, "output_path": str(tmp_path / "text.txt")}),
    ]
    for action, parameters in actions:
        result = action.execute(ctx, parameters)
        assert result.success, (action.name, result.error)
    assert "Page 2 text" in (tmp_path / "text.txt").read_text()
    assert source.read_bytes() == b"%PDF-FAKE"


def test_new_document_actions_are_registered():
    registry = create_action_registry(include_plugins=False)
    for name in ("get_pdf_metadata", "merge_pdf_files", "create_text_document",
                 "get_document_word_frequencies", "export_pdf_text"):
        assert registry.contains(name)
