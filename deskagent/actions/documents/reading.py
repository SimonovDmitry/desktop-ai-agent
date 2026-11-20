from __future__ import annotations

import difflib
import re
from pathlib import Path

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult


def _pages(path: str, limit: int = 100):
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Install pypdf to read PDF documents") from exc
        reader = PdfReader(source)
        return [{"page": index + 1, "text": page.extract_text() or ""}
                for index, page in enumerate(reader.pages[:limit])]
    if source.suffix.lower() in {".txt", ".md", ".rst", ".csv"}:
        return [{"page": 1, "text": source.read_text(encoding="utf-8")}]
    raise ValueError(f"Unsupported document type: {source.suffix}")


class ReadPDFPages(Action):
    name = "read_pdf_pages"
    description = "Read text from a bounded range of PDF pages with page numbers"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "start_page": {"type": "integer", "required": False, "default": 1, "minimum": 1},
        "page_count": {"type": "integer", "required": False, "default": 5, "minimum": 1, "maximum": 50},
    }

    def execute(self, context, parameters):
        try:
            path = Path(parameters["path"]).expanduser().resolve()
            if path.suffix.lower() != ".pdf":
                raise ValueError("A PDF file is required")
            start = parameters.get("start_page", 1)
            count = parameters.get("page_count", 5)
            pages = _pages(str(path), start + count - 1)
            selected = pages[start - 1:start - 1 + count]
            return ActionResult(True, {"path": str(path), "pages": selected, "page_count": len(selected)})
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="DOCUMENT_ERROR")


class SearchInDocument(Action):
    name = "search_in_document"
    description = "Find a phrase in PDF or text pages and return source excerpts"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "query": {"type": "string", "required": True},
        "max_results": {"type": "integer", "required": False, "default": 20, "minimum": 1, "maximum": 100},
    }

    def execute(self, context, parameters):
        try:
            query = parameters["query"].strip()
            if not query:
                raise ValueError("Search query is empty")
            matches = []
            for page in _pages(parameters["path"]):
                text, lowered = page["text"], page["text"].casefold()
                start = 0
                while len(matches) < parameters.get("max_results", 20):
                    index = lowered.find(query.casefold(), start)
                    if index < 0:
                        break
                    matches.append({"page": page["page"], "offset": index,
                                    "excerpt": text[max(0, index - 80):index + len(query) + 80]})
                    start = index + max(1, len(query))
                if len(matches) >= parameters.get("max_results", 20):
                    break
            return ActionResult(True, {"path": parameters["path"], "query": query, "matches": matches})
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="DOCUMENT_ERROR")


class ExtractDocumentTables(Action):
    name = "extract_document_tables"
    description = "Extract structured tables from bounded PDF pages"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "max_pages": {"type": "integer", "required": False, "default": 20, "minimum": 1, "maximum": 100},
    }

    def execute(self, context, parameters):
        try:
            import pdfplumber

            path = Path(parameters["path"]).expanduser().resolve()
            if path.suffix.lower() != ".pdf":
                raise ValueError("A PDF file is required")
            tables = []
            with pdfplumber.open(path) as pdf:
                for number, page in enumerate(pdf.pages[:parameters.get("max_pages", 20)], 1):
                    for table in page.extract_tables() or []:
                        tables.append({"page": number, "rows": table})
            return ActionResult(True, {"path": str(path), "tables": tables})
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="DOCUMENT_ERROR")


class GetDocumentSummary(Action):
    name = "get_document_summary"
    description = "Build a short extractive summary with page references from PDF or text"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "max_sentences": {"type": "integer", "required": False, "default": 5, "minimum": 1, "maximum": 20},
    }

    def execute(self, context, parameters):
        try:
            excerpts = []
            for page in _pages(parameters["path"]):
                sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", page["text"]).strip())
                for sentence in sentences:
                    if len(sentence) >= 40:
                        excerpts.append({"page": page["page"], "text": sentence[:500]})
                    if len(excerpts) >= parameters.get("max_sentences", 5):
                        break
                if len(excerpts) >= parameters.get("max_sentences", 5):
                    break
            return ActionResult(True, {"path": parameters["path"], "method": "extractive", "excerpts": excerpts})
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="DOCUMENT_ERROR")


class CompareDocumentVersions(Action):
    name = "compare_document_versions"
    description = "Show a bounded line-level diff between PDF or text document versions"
    category = ActionCategory.FILE
    parameters_schema = {
        "source": {"type": "string", "required": True},
        "destination": {"type": "string", "required": True},
        "max_diff_lines": {"type": "integer", "required": False, "default": 300, "minimum": 1, "maximum": 2000},
    }

    def execute(self, context, parameters):
        try:
            left = "\n".join(page["text"] for page in _pages(parameters["source"]))
            right = "\n".join(page["text"] for page in _pages(parameters["destination"]))
            diff = list(difflib.unified_diff(
                left.splitlines(), right.splitlines(),
                fromfile=parameters["source"], tofile=parameters["destination"], lineterm="",
            ))
            limit = parameters.get("max_diff_lines", 300)
            return ActionResult(True, {"changed": bool(diff), "diff": diff[:limit], "truncated": len(diff) > limit})
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="DOCUMENT_ERROR")
