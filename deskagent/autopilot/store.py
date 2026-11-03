from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from deskagent.autopilot.models import Session, utc_now
from deskagent.privacy.confirmation import redact


class SessionStore:
    """Transactional persistence for sessions, plan versions and events."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._migrate()
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def _migrate(self):
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    current_step_id TEXT,
                    pending_confirmation_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plan_versions (
                    session_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    plan_json TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, version),
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS session_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event TEXT NOT NULL,
                    step_id TEXT,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_session_events
                    ON session_events(session_id, id);
                CREATE TABLE IF NOT EXISTS workflows (
                    name TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    definition_json TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (name, version)
                );
                """
            )

    def create(self, session: Session) -> Session:
        session.updated_at = utc_now()
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO sessions
                   (id, goal, status, mode, current_step_id, pending_confirmation_json,
                    error, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                self._session_values(session),
            )
            self._insert_plan(session, "initial plan")
            self._append(session.id, "session_created", None, {"goal": session.goal})
        return session

    def save(self, session: Session, event: str | None = None, step_id: str | None = None,
             payload: dict[str, Any] | None = None) -> Session:
        session.updated_at = utc_now()
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """UPDATE sessions SET goal=?, status=?, mode=?, current_step_id=?,
                   pending_confirmation_json=?, error=?, created_at=?, updated_at=? WHERE id=?""",
                (*self._session_values(session)[1:], session.id),
            )
            if not cursor.rowcount:
                raise KeyError(session.id)
            self._connection.execute(
                """INSERT OR REPLACE INTO plan_versions
                   (session_id, version, plan_json, reason, created_at) VALUES (?, ?, ?, ?, ?)""",
                (session.id, session.plan.version, self._json(session.plan.to_dict()), None, utc_now()),
            )
            if event:
                self._append(session.id, event, step_id, payload or {})
        return session

    def save_plan(self, session: Session, reason: str) -> Session:
        with self._lock, self._connection:
            self._insert_plan(session, reason)
            self._append(session.id, "plan_revised", None, {"version": session.plan.version, "reason": reason})
        return self.save(session)

    def get(self, session_id: str) -> Session:
        with self._lock:
            row = self._connection.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
            if not row:
                raise KeyError(session_id)
            plan_row = self._connection.execute(
                "SELECT plan_json FROM plan_versions WHERE session_id=? ORDER BY version DESC LIMIT 1",
                (session_id,),
            ).fetchone()
        value = dict(row)
        value["pending_confirmation"] = self._loads(value.pop("pending_confirmation_json"))
        value["plan"] = self._loads(plan_row["plan_json"])
        return Session.from_dict(value)

    def list(self, statuses: tuple[str, ...] | None = None) -> list[Session]:
        query, parameters = "SELECT id FROM sessions", ()
        if statuses:
            placeholders = ",".join("?" for _ in statuses)
            query += f" WHERE status IN ({placeholders})"
            parameters = statuses
        query += " ORDER BY created_at DESC"
        with self._lock:
            ids = [row["id"] for row in self._connection.execute(query, parameters).fetchall()]
        return [self.get(item) for item in ids]

    def events(self, session_id: str, after_id: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM session_events WHERE session_id=? AND id>? ORDER BY id",
                (session_id, after_id),
            ).fetchall()
        return [
            {**dict(row), "payload": self._loads(row["payload_json"])}
            for row in rows
        ]

    def put_workflow(self, name: str, version: int, definition: dict[str, Any]):
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO workflows (name, version, definition_json, created_at) VALUES (?, ?, ?, ?)",
                (name, version, self._json(definition), utc_now()),
            )

    def get_workflow(self, name: str, version: int | None = None) -> dict[str, Any]:
        query = "SELECT definition_json FROM workflows WHERE name=? AND enabled=1"
        parameters: tuple[Any, ...] = (name,)
        if version is not None:
            query += " AND version=?"
            parameters += (version,)
        query += " ORDER BY version DESC LIMIT 1"
        with self._lock:
            row = self._connection.execute(query, parameters).fetchone()
        if not row:
            raise KeyError(name)
        return self._loads(row["definition_json"])

    def list_workflows(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """SELECT name, MAX(version) AS version FROM workflows
                   WHERE enabled=1 GROUP BY name ORDER BY name"""
            ).fetchall()
        return [{"name": row["name"], "version": row["version"]} for row in rows]

    def close(self):
        with self._lock:
            self._connection.close()

    def _insert_plan(self, session: Session, reason: str):
        self._connection.execute(
            """INSERT INTO plan_versions
               (session_id, version, plan_json, reason, created_at) VALUES (?, ?, ?, ?, ?)""",
            (session.id, session.plan.version, self._json(session.plan.to_dict()), reason, utc_now()),
        )

    def _append(self, session_id: str, event: str, step_id: str | None, payload: dict[str, Any]):
        self._connection.execute(
            """INSERT INTO session_events (session_id, timestamp, event, step_id, payload_json)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, utc_now(), event, step_id, self._json(payload, redact_value=True)),
        )

    def _session_values(self, session: Session) -> tuple[Any, ...]:
        return (
            session.id,
            session.goal,
            session.status.value,
            session.mode.value,
            session.current_step_id,
            self._json(session.pending_confirmation, redact_value=True) if session.pending_confirmation else None,
            session.error,
            session.created_at,
            session.updated_at,
        )

    @staticmethod
    def _json(value: Any, redact_value: bool = False) -> str:
        data = redact(value) if redact_value else value
        return json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)

    @staticmethod
    def _loads(value: str | None) -> Any:
        return json.loads(value) if value else None
