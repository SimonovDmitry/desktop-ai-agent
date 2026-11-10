"""Read-only Apple Notes actions using stable note and folder identifiers."""
from __future__ import annotations

import re
from datetime import datetime

from deskagent.actions.notes._base import (
    NotesAction, bounded_limit, note_id, optional_id, required_text,
)

NOTE = {"note_id": {"type": "string", "required": True}}
FOLDER = {"folder_id": {"type": "string", "required": True}}
LIMIT = {"limit": {"type": "integer", "required": False, "default": 50,
                   "minimum": 1, "maximum": 200}}


class CheckNotesAvailability(NotesAction):
    name = "check_notes_availability"
    description = "Check whether macOS Notes is available without opening a note"
    parameters_schema = {}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call("ping"))


class ListNoteAccounts(NotesAction):
    name = "list_note_accounts"
    description = "List Apple Notes accounts and their default folder identifiers"
    parameters_schema = {}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call("accounts"))


class ListNoteFolders(NotesAction):
    name = "list_note_folders"
    description = "List Apple Notes folders with stable identifiers and containers"
    parameters_schema = {}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call("folders"))


class ListNotes(NotesAction):
    name = "list_notes"
    description = "List bounded note summaries using an offset"
    parameters_schema = {**LIMIT, "offset": {"type": "integer", "required": False, "default": 0, "minimum": 0}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            offset = parameters.get("offset", 0)
            if type(offset) is not int or not 0 <= offset <= 5000:
                raise ValueError("offset must be 0-5000")
            return self._backend(context).call("notes", limit=bounded_limit(parameters), offset=offset)
        return self.run(operation)


class ListFolderNotes(NotesAction):
    name = "list_folder_notes"
    description = "List bounded note summaries in one folder"
    parameters_schema = {**FOLDER, **LIMIT,
                         "offset": {"type": "integer", "required": False, "default": 0, "minimum": 0}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            offset = parameters.get("offset", 0)
            if type(offset) is not int or not 0 <= offset <= 5000:
                raise ValueError("offset must be 0-5000")
            return self._backend(context).call("notes", folder_id=required_text(
                parameters["folder_id"], "folder_id", 512
            ), limit=bounded_limit(parameters), offset=offset)
        return self.run(operation)


class SearchNotes(NotesAction):
    name = "search_notes"
    description = "Search note titles and plaintext without returning full note bodies"
    parameters_schema = {"query": {"type": "string", "required": True}, **LIMIT,
                         "folder_id": {"type": "string", "required": False}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            return self._backend(context).call(
                "search", query=required_text(parameters["query"], "query", 200),
                limit=bounded_limit(parameters),
                folder_id=optional_id(parameters.get("folder_id"), "folder_id"),
            )
        return self.run(operation)


class FindNoteByTitle(NotesAction):
    name = "find_note_by_title"
    description = "Find notes with an exact title and report ambiguity"
    parameters_schema = {"title": {"type": "string", "required": True},
                         "folder_id": {"type": "string", "required": False}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            result = self._backend(context).call(
                "exact_title", title=required_text(parameters["title"], "title", 200),
                folder_id=optional_id(parameters.get("folder_id"), "folder_id"),
            )
            result["unique"] = result["total"] == 1 and not result["truncated"]
            return result
        return self.run(operation)


class GetNote(NotesAction):
    name = "get_note"
    description = "Read note metadata and bounded plaintext by stable id"
    parameters_schema = NOTE
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call("get", note_id=note_id(parameters)))


class GetNoteHtml(NotesAction):
    name = "get_note_html"
    description = "Read bounded original HTML body of one note"
    parameters_schema = NOTE
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call("html", note_id=note_id(parameters)))


class GetNoteAttachments(NotesAction):
    name = "get_note_attachments"
    description = "List attachment metadata without returning attachment bytes"
    parameters_schema = NOTE
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call("attachments", note_id=note_id(parameters)))


class GetSelectedNotes(NotesAction):
    name = "get_selected_notes"
    description = "Read summaries of notes currently selected in Apple Notes"
    parameters_schema = {}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call("selected"))


class GetRecentNotes(NotesAction):
    name = "get_recent_notes"
    description = "List recently modified notes by modification timestamp"
    parameters_schema = {**LIMIT, "folder_id": {"type": "string", "required": False}}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call(
            "recent", limit=bounded_limit(parameters),
            folder_id=optional_id(parameters.get("folder_id"), "folder_id"),
        ))


class CountNotes(NotesAction):
    name = "count_notes"
    description = "Count notes in the scanned Apple Notes library"
    parameters_schema = {"folder_id": {"type": "string", "required": False}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            result = self._backend(context).call(
                "notes", limit=1, offset=0,
                folder_id=optional_id(parameters.get("folder_id"), "folder_id"))
            return {"count": result["matched"], "scanned": result["scanned"],
                    "exact": not result.get("scan_truncated", result["scanned"] >= 5000)}
        return self.run(operation)


class GetFolderNoteCounts(NotesAction):
    name = "get_folder_note_counts"
    description = "Count scanned notes by folder id"
    parameters_schema = {}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call("folder_counts"))


class FindDuplicateNoteTitles(NotesAction):
    name = "find_duplicate_note_titles"
    description = "Find titles shared by multiple notes without reading their bodies"
    parameters_schema = {}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call("duplicate_titles"))


class FindEmptyNotes(NotesAction):
    name = "find_empty_notes"
    description = "Find notes with empty plaintext"
    parameters_schema = {**LIMIT}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: self._backend(context).call(
            "empty", limit=bounded_limit(parameters, default=50)
        ))


class GetNotesModifiedAfter(NotesAction):
    name = "get_notes_modified_after"
    description = "List notes modified after an ISO-8601 timestamp"
    parameters_schema = {"after": {"type": "string", "required": True}, **LIMIT}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            after = parameters["after"]
            parsed = datetime.fromisoformat(after.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("after must include a timezone")
            return self._backend(context).call(
                "modified_after", after=after, limit=bounded_limit(parameters))
        return self.run(operation)


class VerifyNoteContains(NotesAction):
    name = "verify_note_contains"
    description = "Check whether bounded plaintext contains a requested phrase"
    parameters_schema = {**NOTE, "text": {"type": "string", "required": True},
                         "case_sensitive": {"type": "boolean", "required": False, "default": False}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            note = self._backend(context).call("get", note_id=note_id(parameters))
            query = required_text(parameters["text"], "text", 1000)
            content = note["text"]
            found = query in content if parameters.get("case_sensitive") else query.casefold() in content.casefold()
            return {"note_id": note["id"], "found": found,
                    "complete_text_checked": not note.get("text_truncated", False)}
        return self.run(operation)


class GetNoteStatistics(NotesAction):
    name = "get_note_statistics"
    description = "Count characters, words and lines in bounded note plaintext"
    parameters_schema = NOTE
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            note = self._backend(context).call("get", note_id=note_id(parameters))
            text = note["text"]
            return {"note_id": note["id"], "characters": len(text),
                    "words": len(re.findall(r"\w+", text)), "lines": len(text.splitlines()),
                    "partial": note.get("text_truncated", False)}
        return self.run(operation)


class ExtractNoteLinks(NotesAction):
    name = "extract_note_links"
    description = "Extract bounded HTTP links from note plaintext"
    parameters_schema = NOTE
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            note = self._backend(context).call("get", note_id=note_id(parameters))
            found = re.findall(r"https?://[^\s<>)]+", note["text"])
            return {"note_id": note["id"], "links": found[:100],
                    "truncated": len(found) > 100 or note.get("text_truncated", False)}
        return self.run(operation)


class GetNoteTextExcerpt(NotesAction):
    name = "get_note_text_excerpt"
    description = "Read a bounded excerpt around a phrase in note plaintext"
    parameters_schema = {**NOTE, "query": {"type": "string", "required": True},
                         "context_chars": {"type": "integer", "required": False,
                                           "default": 100, "minimum": 0, "maximum": 1000}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            note = self._backend(context).call("get", note_id=note_id(parameters))
            query = required_text(parameters["query"], "query", 200)
            context_chars = parameters.get("context_chars", 100)
            if type(context_chars) is not int or not 0 <= context_chars <= 1000:
                raise ValueError("context_chars must be 0-1000")
            index = note["text"].casefold().find(query.casefold())
            excerpt = None
            if index >= 0:
                excerpt = note["text"][max(0, index - context_chars):index + len(query) + context_chars]
            return {"note_id": note["id"], "found": index >= 0,
                    "excerpt": excerpt,
                    "complete_text_checked": not note.get("text_truncated", False)}
        return self.run(operation)


class CompareNotes(NotesAction):
    name = "compare_notes"
    description = "Compare bounded plaintext of two notes"
    parameters_schema = {"first_note_id": {"type": "string", "required": True},
                         "second_note_id": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            backend = self._backend(context)
            first = backend.call("get", note_id=required_text(parameters["first_note_id"], "first_note_id", 512))
            second = backend.call("get", note_id=required_text(parameters["second_note_id"], "second_note_id", 512))
            complete = not first.get("text_truncated", False) and not second.get("text_truncated", False)
            return {"first_note_id": first["id"], "second_note_id": second["id"],
                    "identical_text": first["text"] == second["text"],
                    "complete_text_compared": complete, "first_characters": len(first["text"]),
                    "second_characters": len(second["text"])}
        return self.run(operation)
