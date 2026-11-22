"""Action wrappers for portable platform operations."""
from __future__ import annotations

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.platform.common import documents as portable
from deskagent.platform.common.documents import (  # noqa: F401
    MAX_FILE_BYTES,
    MAX_TEXT_CHARS,
    MAX_PAGES,
    TEXT_EXTENSIONS,
    _guard,
    page_range,
)


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


def source_path(context, value, extensions=None):
    service = getattr(getattr(context, "services", None), "documents", None)
    return (service or portable.DocumentService()).source_path(context, value, extensions)


def output_path(context, value, extensions):
    service = getattr(getattr(context, "services", None), "documents", None)
    return (service or portable.DocumentService()).output_path(context, value, extensions)


def read_text(context, value):
    service = getattr(getattr(context, "services", None), "documents", None)
    return (service or portable.DocumentService()).read_text(context, value)


def save_new(context, value, suffixes, writer):
    service = getattr(getattr(context, "services", None), "documents", None)
    return (service or portable.DocumentService()).save_new(context, value, suffixes, writer)


def pdf_reader(context, value):
    service = getattr(getattr(context, "services", None), "documents", None)
    return (service or portable.DocumentService()).pdf_reader(context, value)


def pdf_writer(context=None):
    service = getattr(getattr(context, "services", None), "documents", None)
    return (service or portable.DocumentService()).pdf_writer()
