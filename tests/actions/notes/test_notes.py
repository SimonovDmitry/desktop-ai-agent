import json
from pathlib import Path
from types import SimpleNamespace

from deskagent.actions.notes._base import NotesAction
from deskagent.actions.notes.backend import NotesBackend, SCRIPT
from deskagent.actions.notes import reading, writing
from deskagent.actions.registry import create_action_registry
from deskagent.core.config import SecuritySettings, Settings


def context(tmp_path):
    return SimpleNamespace(settings=Settings(
        security=SecuritySettings(allowed_paths=[str(tmp_path)], blocked_paths=[])
    ))


class FakeBackend:
    def __init__(self):
        self.calls = []
        self.notes = {
            "n1": {"id": "n1", "title": "Meeting", "folder_id": "f1",
                   "text": "Meeting\nDiscuss budget. https://example.com",
                   "html": "<div>Meeting</div><div>Discuss budget.</div>",
                   "text_truncated": False, "html_truncated": False},
            "n2": {"id": "n2", "title": "Meeting", "folder_id": "f1",
                   "text": "Meeting\nOther notes", "html": "<div>Meeting</div>",
                   "text_truncated": False, "html_truncated": False},
        }

    def call(self, op, **kwargs):
        self.calls.append((op, kwargs))
        if op == "ping":
            return {"available": True, "running": False}
        if op == "accounts":
            return {"accounts": [{"id": "a1", "name": "iCloud"}], "total": 1, "truncated": False}
        if op == "folders":
            return {"folders": [{"id": "f1", "name": "Work"}], "total": 1, "truncated": False}
        if op == "notes":
            items = [item for item in self.notes.values()
                     if not kwargs.get("folder_id") or item["folder_id"] == kwargs["folder_id"]]
            return {"notes": items[kwargs["offset"]:kwargs["offset"] + kwargs["limit"]],
                    "matched": len(items), "scanned": len(items), "truncated": False}
        if op == "search":
            items = [item for item in self.notes.values()
                     if kwargs["query"].casefold() in item["text"].casefold()]
            return {"notes": items[:kwargs["limit"]], "total": len(items), "truncated": False}
        if op == "exact_title":
            items = [item for item in self.notes.values() if item["title"] == kwargs["title"]]
            return {"notes": items, "total": len(items), "truncated": False}
        if op in {"get", "html"}:
            return dict(self.notes[kwargs["note_id"]])
        if op == "attachments":
            return {"note_id": kwargs["note_id"], "attachments": [], "total": 0}
        if op == "selected":
            return {"notes": [self.notes["n1"]], "total": 1}
        if op in {"recent", "empty", "modified_after"}:
            return {"notes": [self.notes["n1"]], "total": 1, "truncated": False}
        if op == "folder_counts":
            return {"counts": {"f1": 2}, "scanned": 2, "truncated": False}
        if op == "duplicate_titles":
            return {"duplicates": [{"title": "meeting", "note_ids": ["n1", "n2"]}],
                    "scanned": 2, "truncated": False}
        if op == "create":
            return {"id": "new", "created": True, "title": kwargs["title"]}
        if op == "create_folder":
            return {"id": "new-folder", "created": True, "name": kwargs["name"]}
        if op in {"rename", "append", "prepend", "move", "duplicate", "show"}:
            return {"id": kwargs["note_id"], "operation": op, "verified": True}
        raise AssertionError(op)


def test_read_actions_and_analysis(tmp_path, monkeypatch):
    backend = FakeBackend()
    monkeypatch.setattr(NotesAction, "backend", staticmethod(lambda: backend))
    ctx = context(tmp_path)
    actions = [
        (reading.CheckNotesAvailability(), {}),
        (reading.ListNoteAccounts(), {}),
        (reading.ListNoteFolders(), {}),
        (reading.ListNotes(), {}),
        (reading.ListFolderNotes(), {"folder_id": "f1"}),
        (reading.SearchNotes(), {"query": "budget"}),
        (reading.FindNoteByTitle(), {"title": "Meeting"}),
        (reading.GetNote(), {"note_id": "n1"}),
        (reading.GetNoteHtml(), {"note_id": "n1"}),
        (reading.GetNoteAttachments(), {"note_id": "n1"}),
        (reading.GetSelectedNotes(), {}),
        (reading.GetRecentNotes(), {}),
        (reading.CountNotes(), {}),
        (reading.GetFolderNoteCounts(), {}),
        (reading.FindDuplicateNoteTitles(), {}),
        (reading.FindEmptyNotes(), {}),
        (reading.GetNotesModifiedAfter(), {"after": "2026-01-01T00:00:00+00:00"}),
        (reading.VerifyNoteContains(), {"note_id": "n1", "text": "budget"}),
        (reading.GetNoteStatistics(), {"note_id": "n1"}),
        (reading.ExtractNoteLinks(), {"note_id": "n1"}),
        (reading.GetNoteTextExcerpt(), {"note_id": "n1", "query": "budget"}),
        (reading.CompareNotes(), {"first_note_id": "n1", "second_note_id": "n2"}),
    ]
    results = {}
    for action, params in actions:
        result = action.execute(ctx, params)
        assert result.success, (action.name, result.error)
        results[action.name] = result.data
    assert results["count_notes"]["count"] == 2
    assert not results["find_note_by_title"]["unique"]
    assert results["verify_note_contains"]["found"]
    assert results["extract_note_links"]["links"] == ["https://example.com"]
    assert results["get_note_text_excerpt"]["found"]
    assert not results["compare_notes"]["identical_text"]


def test_write_actions_and_export_safety(tmp_path, monkeypatch):
    backend = FakeBackend()
    monkeypatch.setattr(NotesAction, "backend", staticmethod(lambda: backend))
    ctx = context(tmp_path)
    actions = [
        (writing.CreateNote(), {"title": "New", "text": "body"}),
        (writing.CreateNoteFolder(), {"name": "Projects"}),
        (writing.RenameNote(), {"note_id": "n1", "title": "Renamed"}),
        (writing.AppendToNote(), {"note_id": "n1", "text": "More"}),
        (writing.PrependToNote(), {"note_id": "n1", "text": "Before"}),
        (writing.MoveNote(), {"note_id": "n1", "folder_id": "f1"}),
        (writing.DuplicateNote(), {"note_id": "n1"}),
        (writing.ShowNote(), {"note_id": "n1"}),
    ]
    for action, params in actions:
        result = action.execute(ctx, params)
        assert result.success, (action.name, result.error)
    text = writing.ExportNoteText().execute(ctx, {
        "note_id": "n1", "output_path": str(tmp_path / "note.txt"),
    })
    html = writing.ExportNoteHtml().execute(ctx, {
        "note_id": "n1", "output_path": str(tmp_path / "note.html"),
    })
    assert text.success and html.success
    assert "Discuss budget" in Path(text.data["path"]).read_text()
    assert "<div>Meeting" in Path(html.data["path"]).read_text()
    collision = writing.ExportNoteText().execute(ctx, {
        "note_id": "n1", "output_path": str(tmp_path / "note.txt"),
    })
    outside = writing.ExportNoteText().execute(ctx, {
        "note_id": "n1", "output_path": str(tmp_path.parent / "outside.txt"),
    })
    assert not collision.success and not outside.success
    assert not writing.CreateNote().execute(ctx, {"title": ""}).success


def test_fixed_jxa_script_keeps_input_out_of_code(monkeypatch):
    monkeypatch.setattr("deskagent.actions.notes.backend.platform.system", lambda: "Darwin")
    monkeypatch.setattr("deskagent.actions.notes.backend.Path.is_dir", lambda self: True)
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        return SimpleNamespace(returncode=0, stdout='{"available":true}', stderr="")

    monkeypatch.setattr("deskagent.actions.notes.backend.subprocess.run", fake_run)
    content = 'A "quote"; app.notes().delete()'
    result = NotesBackend().call("create", title=content, text="safe")
    assert result["available"]
    assert content not in SCRIPT
    assert json.loads(captured["command"][-1])["title"] == content
    assert captured["command"][-2] == SCRIPT


def test_note_actions_are_registered():
    registry = create_action_registry(include_plugins=False)
    for name in ("list_notes", "search_notes", "create_note", "append_to_note",
                 "move_note", "export_note_html"):
        assert registry.contains(name)
