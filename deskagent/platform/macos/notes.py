"""Apple Notes adapter using fixed JXA operations and structured arguments."""
from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

from deskagent.platform.base.notes import NotesService

NOTES_APP = "/System/Applications/Notes.app"
MAX_ARGUMENT_BYTES = 60_000
MAX_RESPONSE_BYTES = 2_000_000

SCRIPT = r"""
function run(argv) {
  const p = JSON.parse(argv[0] || "{}");
  const app = Application("/System/Applications/Notes.app");
  const scanLimit = 5000;
  function value(fn, fallback) { try { return fn(); } catch (_) { return fallback; } }
  function idOf(item) { return String(value(() => item.id(), "")); }
  function textOf(item) { return String(value(() => item.plaintext(), "")); }
  function bodyOf(item) { return String(value(() => item.body(), "")); }
  function safeDate(item, key) {
    return value(() => {
      const date = item[key]();
      return date && date.toISOString ? date.toISOString() : String(date);
    }, "");
  }
  function noteById(id) {
    const notes = app.notes();
    for (let i = 0; i < Math.min(notes.length, scanLimit); i++)
      if (idOf(notes[i]) === id) return notes[i];
    throw new Error("Note not found by id");
  }
  function folderById(id) {
    const folders = app.folders();
    for (let i = 0; i < Math.min(folders.length, scanLimit); i++)
      if (idOf(folders[i]) === id) return folders[i];
    throw new Error("Folder not found by id");
  }
  function accountById(id) {
    const accounts = app.accounts();
    for (let i = 0; i < Math.min(accounts.length, scanLimit); i++)
      if (idOf(accounts[i]) === id) return accounts[i];
    throw new Error("Account not found by id");
  }
  function noteInfo(note) {
    const folder = value(() => note.container(), null);
    return {
      id: idOf(note), title: String(value(() => note.name(), "")),
      folder_id: folder ? idOf(folder) : null,
      created_at: safeDate(note, "creationDate"),
      modified_at: safeDate(note, "modificationDate"),
      locked: Boolean(value(() => note.passwordProtected(), false)),
      shared: Boolean(value(() => note.shared(), false))
    };
  }
  function folderInfo(folder) {
    const container = value(() => folder.container(), null);
    return {id: idOf(folder), name: String(value(() => folder.name(), "")),
            container_id: container ? idOf(container) : null,
            shared: Boolean(value(() => folder.shared(), false))};
  }
  function escapeHtml(text) {
    return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function htmlLines(text) { return escapeHtml(text).replace(/\r\n?/g, "\n").replace(/\n/g, "<br>"); }
  function ensureEditable(note) {
    if (Boolean(note.passwordProtected())) throw new Error("Locked note cannot be edited");
    if (Boolean(note.shared())) throw new Error("Shared note cannot be edited");
    if (note.attachments().length > 0) throw new Error("Note with attachments cannot be edited");
  }
  function insertHtml(body, fragment, prepend) {
    if (prepend) {
      const match = body.match(/<body[^>]*>/i);
      return match ? body.slice(0, match.index + match[0].length) + fragment +
        body.slice(match.index + match[0].length) : fragment + body;
    }
    const match = body.match(/<\/body>/i);
    return match ? body.slice(0, match.index) + fragment + body.slice(match.index) : body + fragment;
  }
  let result;
  switch (p.op) {
    case "ping":
      result = {available: true, running: app.running()};
      break;
    case "accounts": {
      const items = app.accounts();
      result = {accounts: items.slice(0, 200).map(a => ({
        id: idOf(a), name: String(value(() => a.name(), "")),
        default_folder_id: idOf(value(() => a.defaultFolder(), null))
      })), total: items.length, truncated: items.length > 200};
      break;
    }
    case "folders": {
      const items = app.folders();
      result = {folders: items.slice(0, 500).map(folderInfo), total: items.length,
                truncated: items.length > 500};
      break;
    }
    case "notes": {
      const notes = app.notes();
      const found = [];
      let matched = 0;
      for (let i = 0; i < Math.min(notes.length, scanLimit); i++) {
        const info = noteInfo(notes[i]);
        if (p.folder_id && info.folder_id !== p.folder_id) continue;
        if (matched++ < p.offset) continue;
        if (found.length < p.limit) found.push(info);
      }
      result = {notes: found, matched: matched, scanned: Math.min(notes.length, scanLimit),
                scan_truncated: notes.length > scanLimit,
                truncated: notes.length > scanLimit || matched > p.offset + found.length};
      break;
    }
    case "search": {
      const notes = app.notes();
      const found = [];
      let total = 0;
      const query = String(p.query).toLocaleLowerCase();
      for (let i = 0; i < Math.min(notes.length, scanLimit); i++) {
        const note = notes[i];
        const info = noteInfo(note);
        if (p.folder_id && info.folder_id !== p.folder_id) continue;
        const plain = textOf(note);
        if ((info.title + "\n" + plain).toLocaleLowerCase().indexOf(query) < 0) continue;
        total++;
        if (found.length < p.limit) found.push(Object.assign(info, {excerpt: plain.slice(0, 300)}));
      }
      result = {notes: found, total: total, scanned: Math.min(notes.length, scanLimit),
                truncated: notes.length > scanLimit || total > found.length};
      break;
    }
    case "exact_title": {
      const notes = app.notes();
      const found = [];
      let total = 0;
      for (let i = 0; i < Math.min(notes.length, scanLimit); i++) {
        const info = noteInfo(notes[i]);
        if (info.title !== p.title || (p.folder_id && info.folder_id !== p.folder_id)) continue;
        total++;
        if (found.length < 100) found.push(info);
      }
      result = {notes: found, total: total, scanned: Math.min(notes.length, scanLimit),
                truncated: notes.length > scanLimit || total > found.length};
      break;
    }
    case "recent": {
      const notes = app.notes();
      const found = [];
      for (let i = 0; i < Math.min(notes.length, scanLimit); i++) {
        const info = noteInfo(notes[i]);
        if (!p.folder_id || info.folder_id === p.folder_id) found.push(info);
      }
      found.sort((a, b) => b.modified_at.localeCompare(a.modified_at));
      result = {notes: found.slice(0, p.limit), scanned: Math.min(notes.length, scanLimit),
                truncated: notes.length > scanLimit || found.length > p.limit};
      break;
    }
    case "folder_counts": {
      const notes = app.notes();
      const counts = {};
      for (let i = 0; i < Math.min(notes.length, scanLimit); i++) {
        const folder = noteInfo(notes[i]).folder_id || "unknown";
        counts[folder] = (counts[folder] || 0) + 1;
      }
      result = {counts: counts, scanned: Math.min(notes.length, scanLimit),
                truncated: notes.length > scanLimit};
      break;
    }
    case "duplicate_titles": {
      const notes = app.notes();
      const groups = {};
      for (let i = 0; i < Math.min(notes.length, scanLimit); i++) {
        const info = noteInfo(notes[i]);
        const key = info.title.toLocaleLowerCase();
        if (!key) continue;
        if (!groups[key]) groups[key] = [];
        groups[key].push(info.id);
      }
      const duplicates = Object.keys(groups).filter(key => groups[key].length > 1)
        .slice(0, 100).map(key => ({title: key, note_ids: groups[key]}));
      result = {duplicates: duplicates, scanned: Math.min(notes.length, scanLimit),
                truncated: notes.length > scanLimit};
      break;
    }
    case "empty": {
      const notes = app.notes();
      const found = [];
      let total = 0;
      for (let i = 0; i < Math.min(notes.length, scanLimit); i++) {
        const info = noteInfo(notes[i]);
        if (textOf(notes[i]).trim() === "") {
          total++;
          if (found.length < p.limit) found.push(info);
        }
      }
      result = {notes: found, total: total, scanned: Math.min(notes.length, scanLimit),
                truncated: notes.length > scanLimit || total > found.length};
      break;
    }
    case "modified_after": {
      const notes = app.notes();
      const found = [];
      let total = 0;
      for (let i = 0; i < Math.min(notes.length, scanLimit); i++) {
        const info = noteInfo(notes[i]);
        if (info.modified_at && new Date(info.modified_at).getTime() > new Date(p.after).getTime()) {
          total++;
          if (found.length < p.limit) found.push(info);
        }
      }
      result = {notes: found, total: total, scanned: Math.min(notes.length, scanLimit),
                truncated: notes.length > scanLimit || total > found.length};
      break;
    }
    case "get": {
      const note = noteById(p.note_id);
      const plain = textOf(note);
      result = Object.assign(noteInfo(note), {text: plain.slice(0, 20000),
                                              text_truncated: plain.length > 20000});
      break;
    }
    case "html": {
      const note = noteById(p.note_id);
      const html = bodyOf(note);
      result = Object.assign(noteInfo(note), {html: html.slice(0, 100000),
                                              html_truncated: html.length > 100000});
      break;
    }
    case "attachments": {
      const note = noteById(p.note_id);
      const items = value(() => note.attachments(), []);
      result = {note_id: p.note_id, attachments: items.slice(0, 200).map(a => ({
        id: idOf(a), name: String(value(() => a.name(), "")),
        url: String(value(() => a.URL(), ""))
      })), total: items.length, truncated: items.length > 200};
      break;
    }
    case "selected": {
      const notes = value(() => app.selection(), []);
      result = {notes: notes.slice(0, 100).map(noteInfo), total: notes.length};
      break;
    }
    case "create": {
      const folder = p.folder_id ? folderById(p.folder_id) : app.defaultAccount().defaultFolder();
      const html = "<div><b>" + htmlLines(p.title) + "</b></div><div>" +
        htmlLines(p.text) + "</div>";
      const created = app.Note({body: html});
      folder.notes.push(created);
      const note = folder.notes[0];
      if (String(note.plaintext()).indexOf(p.title) < 0) throw new Error("Created note could not be verified");
      result = Object.assign(noteInfo(note), {created: true});
      break;
    }
    case "create_folder": {
      const account = p.account_id ? accountById(p.account_id) : app.defaultAccount();
      const folder = app.Folder({name: p.name});
      account.folders.push(folder);
      const created = account.folders[0];
      if (String(created.name()) !== p.name)
        throw new Error("Created folder could not be verified");
      result = Object.assign(folderInfo(created), {created: true});
      break;
    }
    case "rename": {
      const note = noteById(p.note_id);
      ensureEditable(note);
      note.name = p.title;
      if (String(note.name()) !== p.title)
        throw new Error("Note rename could not be verified");
      result = Object.assign(noteInfo(note), {renamed: true});
      break;
    }
    case "append":
    case "prepend": {
      const note = noteById(p.note_id);
      ensureEditable(note);
      const before = String(note.plaintext());
      const fragment = "<div>" + htmlLines(p.text) + "</div>";
      note.body = insertHtml(String(note.body()), fragment, p.op === "prepend");
      const after = String(note.plaintext());
      const normalized = text => text.replace(/\s+/g, " ").trim();
      if (normalized(after).indexOf(normalized(p.text)) < 0 || after === before)
        throw new Error("Note text update could not be verified");
      result = Object.assign(noteInfo(note), {updated: true, characters: after.length});
      break;
    }
    case "move": {
      const note = noteById(p.note_id);
      ensureEditable(note);
      const folder = folderById(p.folder_id);
      app.move(note, {to: folder});
      if (idOf(note.container()) !== p.folder_id) throw new Error("Note move could not be verified");
      result = Object.assign(noteInfo(note), {moved: true});
      break;
    }
    case "duplicate": {
      const note = noteById(p.note_id);
      if (Boolean(note.passwordProtected()) || note.attachments().length > 0)
        throw new Error("Locked or attachment-bearing note cannot be duplicated");
      const folder = p.folder_id ? folderById(p.folder_id) : note.container();
      const copy = app.Note({body: String(note.body())});
      folder.notes.push(copy);
      const created = folder.notes[0];
      if (String(created.plaintext()) !== String(note.plaintext()))
        throw new Error("Duplicate note could not be verified");
      result = Object.assign(noteInfo(created), {source_id: p.note_id, duplicated: true});
      break;
    }
    case "show": {
      const note = noteById(p.note_id);
      app.show(note);
      result = Object.assign(noteInfo(note), {shown: true});
      break;
    }
    default:
      throw new Error("Unsupported Notes operation");
  }
  return JSON.stringify(result);
}
"""


class NotesBackend(NotesService):
    def __init__(self, timeout=45):
        self.timeout = timeout

    def call(self, op, **parameters):
        if platform.system() != "Darwin" or not Path(NOTES_APP).is_dir():
            raise RuntimeError("Apple Notes actions require macOS Notes")
        payload = json.dumps({"op": op, **parameters}, ensure_ascii=False)
        if len(payload.encode("utf-8")) > MAX_ARGUMENT_BYTES:
            raise ValueError("Notes request exceeds 60 KB")
        result = subprocess.run(
            ["/usr/bin/osascript", "-l", "JavaScript", "-e", SCRIPT, payload],
            capture_output=True, text=True, timeout=self.timeout, check=False,
        )
        if result.returncode:
            message = result.stderr.strip()[:1000] or "Apple Notes automation failed"
            raise RuntimeError(message)
        if len(result.stdout.encode("utf-8")) > MAX_RESPONSE_BYTES:
            raise ValueError("Notes response exceeds 2 MB")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Apple Notes returned an invalid response") from exc
