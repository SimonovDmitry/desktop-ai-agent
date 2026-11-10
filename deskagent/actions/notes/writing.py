"""Apple Notes creation, editing, navigation and safe export actions."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from deskagent.actions.notes._base import (
    NotesAction, NotesWriteAction, note_id, optional_id, required_text,
)
from deskagent.actions.types import RiskLevel
from deskagent.privacy.guards import FilesystemGuard

NOTE = {"note_id": {"type": "string", "required": True}}


class CreateNote(NotesWriteAction):
    name = "create_note"
    description = "Create a plain-text Apple Note in a selected or default folder"
    parameters_schema = {"title": {"type": "string", "required": True},
                         "text": {"type": "string", "required": False, "default": ""},
                         "folder_id": {"type": "string", "required": False}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            text = parameters.get("text", "")
            if not isinstance(text, str) or len(text) > 20000:
                raise ValueError("text must contain at most 20,000 characters")
            return self._backend(context).call(
                "create", title=required_text(parameters["title"], "title", 200),
                text=text, folder_id=optional_id(parameters.get("folder_id"), "folder_id"),
            )
        return self.run(operation)


class CreateNoteFolder(NotesWriteAction):
    name = "create_note_folder"
    description = "Create an Apple Notes folder in a selected or default account"
    parameters_schema = {"name": {"type": "string", "required": True},
                         "account_id": {"type": "string", "required": False}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call(
            "create_folder", name=required_text(parameters["name"], "name", 200),
            account_id=optional_id(parameters.get("account_id"), "account_id"),
        ))


class RenameNote(NotesWriteAction):
    name = "rename_note"
    description = "Rename an editable Apple Note by stable id"
    parameters_schema = {**NOTE, "title": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call(
            "rename", note_id=note_id(parameters),
            title=required_text(parameters["title"], "title", 200),
        ))


class AppendToNote(NotesWriteAction):
    name = "append_to_note"
    description = "Append escaped text to an editable note and verify the new content"
    parameters_schema = {**NOTE, "text": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call(
            "append", note_id=note_id(parameters),
            text=required_text(parameters["text"], "text", 10000),
        ))


class PrependToNote(NotesWriteAction):
    name = "prepend_to_note"
    description = "Prepend escaped text to an editable note and verify the new content"
    parameters_schema = {**NOTE, "text": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call(
            "prepend", note_id=note_id(parameters),
            text=required_text(parameters["text"], "text", 10000),
        ))


class MoveNote(NotesWriteAction):
    name = "move_note"
    description = "Move an editable note to a folder by stable id and verify location"
    parameters_schema = {**NOTE, "folder_id": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call(
            "move", note_id=note_id(parameters),
            folder_id=required_text(parameters["folder_id"], "folder_id", 512),
        ))


class DuplicateNote(NotesWriteAction):
    name = "duplicate_note"
    description = "Copy an attachment-free note to a selected or current folder"
    parameters_schema = {**NOTE, "folder_id": {"type": "string", "required": False}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call(
            "duplicate", note_id=note_id(parameters),
            folder_id=optional_id(parameters.get("folder_id"), "folder_id"),
        ))


class ShowNote(NotesAction):
    name = "show_note"
    description = "Show an Apple Note in the Notes application by stable id"
    risk_level = RiskLevel.LOW
    parameters_schema = NOTE
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call("show", note_id=note_id(parameters)))


def _export(context, target_value, content, suffix):
    target = Path(target_value).expanduser().resolve()
    if target.suffix.lower() != suffix:
        raise ValueError(f"Output path must end with {suffix}")
    security = context.settings.security
    decision = FilesystemGuard(security.allowed_paths, security.blocked_paths).check(
        "write_file", {"output_path": str(target)}
    )
    if not decision.allowed:
        raise PermissionError(decision.reason)
    if target.exists():
        raise FileExistsError(f"Output file already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".deskagent-note-", suffix=suffix, dir=target.parent)
    os.close(descriptor)
    try:
        Path(temporary).write_text(content, encoding="utf-8")
        os.link(temporary, target)
        return {"path": str(target), "bytes": target.stat().st_size}
    finally:
        Path(temporary).unlink(missing_ok=True)


class ExportNoteText(NotesWriteAction):
    name = "export_note_text"
    description = "Export complete note plaintext to a new UTF-8 text file"
    parameters_schema = {**NOTE, "output_path": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            note = self._backend(context).call("get", note_id=note_id(parameters))
            if note.get("text_truncated"):
                raise ValueError("Note exceeds export limit of 20,000 characters")
            return {"note_id": note["id"], **_export(context, parameters["output_path"], note["text"], ".txt")}
        return self.run(operation)


class ExportNoteHtml(NotesWriteAction):
    name = "export_note_html"
    description = "Export complete note HTML body to a new UTF-8 HTML file"
    parameters_schema = {**NOTE, "output_path": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            note = self._backend(context).call("html", note_id=note_id(parameters))
            if note.get("html_truncated"):
                raise ValueError("Note exceeds HTML export limit of 100,000 characters")
            return {"note_id": note["id"], **_export(context, parameters["output_path"], note["html"], ".html")}
        return self.run(operation)
