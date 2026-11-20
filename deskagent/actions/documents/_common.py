"""Bounded and policy-aware document primitives."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.privacy.guards import FilesystemGuard

MAX_FILE_BYTES = 25_000_000
MAX_TEXT_CHARS = 2_000_000
MAX_PAGES = 500
TEXT_EXTENSIONS = {".txt", ".md", ".rst"}


class DocumentAction(Action):
    discoverable = False
    category = ActionCategory.FILE

    @staticmethod
    def run(operation):
        try:
            return ActionResult(True, operation())
        except (ValueError, FileNotFoundError, FileExistsError, PermissionError, UnicodeError) as exc:
            return ActionResult(False, error=str(exc), error_code="DOCUMENT_ERROR")
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="DOCUMENT_ERROR")


class DocumentWriteAction(DocumentAction):
    discoverable = False
    risk_level = RiskLevel.MEDIUM
    reversible = True


def _guard(context):
    security = context.settings.security
    return FilesystemGuard(security.allowed_paths, security.blocked_paths)


def source_path(context, value, extensions=None):
    path = Path(value).expanduser().resolve()
    if extensions and path.suffix.lower() not in extensions:
        raise ValueError(f"Expected one of: {', '.join(sorted(extensions))}")
    decision = _guard(context).check("read_file", {"path": str(path)})
    if not decision.allowed:
        raise PermissionError(decision.reason)
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Document exceeds 25 MB processing limit")
    return path


def output_path(context, value, extensions):
    path = Path(value).expanduser().resolve()
    if path.suffix.lower() not in extensions:
        raise ValueError(f"Output must end with one of: {', '.join(sorted(extensions))}")
    decision = _guard(context).check("write_file", {"output_path": str(path)})
    if not decision.allowed:
        raise PermissionError(decision.reason)
    if path.exists():
        raise FileExistsError(f"Output file already exists: {path}")
    return path


def read_text(context, value):
    path = source_path(context, value, TEXT_EXTENSIONS)
    text = path.read_bytes().decode("utf-8-sig")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError("Document exceeds 2 million character processing limit")
    return path, text


def save_new(context, value, suffixes, writer):
    target = output_path(context, value, suffixes)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".deskagent-document-", suffix=target.suffix, dir=target.parent)
    os.close(descriptor)
    try:
        writer(Path(temporary))
        size = Path(temporary).stat().st_size
        if size > MAX_FILE_BYTES:
            raise ValueError("Output exceeds 25 MB processing limit")
        os.link(temporary, target)
        return {"path": str(target), "bytes": size}
    finally:
        Path(temporary).unlink(missing_ok=True)


def pdf_reader(context, value):
    path = source_path(context, value, {".pdf"})
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to process PDF documents") from exc
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF is unsupported by this action")
    if len(reader.pages) > MAX_PAGES:
        raise ValueError("PDF exceeds 500 page processing limit")
    return path, reader


def pdf_writer():
    try:
        from pypdf import PdfWriter
    except ImportError as exc:
        raise RuntimeError("Install pypdf to write PDF documents") from exc
    return PdfWriter()


def page_range(parameters, total, *, start_key="start_page", count_key="page_count"):
    start = parameters.get(start_key, 1)
    count = parameters.get(count_key, min(10, total))
    if not isinstance(start, int) or not isinstance(count, int) or start < 1 or count < 1:
        raise ValueError("Page numbers must be positive integers")
    if start > total or start + count - 1 > total:
        raise ValueError("Page range is outside the PDF")
    return range(start - 1, start - 1 + count)
