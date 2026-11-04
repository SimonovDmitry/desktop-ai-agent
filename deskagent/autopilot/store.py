from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from deskagent.autopilot.models import Plan, Session, StepStatus, utc_now
from deskagent.privacy.confirmation import redact


class LeaseConflict(RuntimeError):
    pass


class SessionStore:
    """Transactional state store with immutable plans and normalized runtime records."""

    SESSION_COLUMNS = {
        "action_count": "INTEGER NOT NULL DEFAULT 0",
        "replan_count": "INTEGER NOT NULL DEFAULT 0",
        "max_replans": "INTEGER NOT NULL DEFAULT 3",
        "max_duration_seconds": "REAL NOT NULL DEFAULT 3600",
        "started_at": "TEXT",
        "approved_plan_hash": "TEXT",
        "owner_id": "TEXT",
        "lease_expires_at": "TEXT",
    }

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
                    id TEXT PRIMARY KEY, goal TEXT NOT NULL, status TEXT NOT NULL,
                    mode TEXT NOT NULL, current_step_id TEXT, pending_confirmation_json TEXT,
                    error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plan_versions (
                    session_id TEXT NOT NULL, version INTEGER NOT NULL,
                    plan_json TEXT NOT NULL, reason TEXT, created_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, version),
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS steps (
                    session_id TEXT NOT NULL, step_id TEXT NOT NULL, plan_version INTEGER NOT NULL,
                    status TEXT NOT NULL, runtime_json TEXT NOT NULL, updated_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, step_id),
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS step_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                    step_id TEXT NOT NULL, attempt INTEGER NOT NULL, status TEXT NOT NULL,
                    started_at TEXT NOT NULL, finished_at TEXT, error_code TEXT, error TEXT,
                    UNIQUE(session_id, step_id, attempt)
                );
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL, step_id TEXT NOT NULL,
                    attempt INTEGER NOT NULL, action TEXT NOT NULL, arguments_json TEXT NOT NULL,
                    idempotency_key TEXT, status TEXT NOT NULL, result_json TEXT,
                    started_at TEXT NOT NULL, finished_at TEXT
                );
                DROP INDEX IF EXISTS idx_tool_idempotency;
                CREATE INDEX IF NOT EXISTS idx_tool_idempotency
                    ON tool_calls(idempotency_key, status) WHERE idempotency_key IS NOT NULL;
                CREATE TABLE IF NOT EXISTS verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                    step_id TEXT NOT NULL, attempt INTEGER NOT NULL, kind TEXT NOT NULL,
                    success INTEGER NOT NULL, details_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    confirmation_id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                    step_id TEXT, plan_version INTEGER NOT NULL, scope_hash TEXT NOT NULL,
                    request_json TEXT NOT NULL, answer_json TEXT, status TEXT NOT NULL,
                    created_at TEXT NOT NULL, answered_at TEXT
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                    step_id TEXT, kind TEXT NOT NULL, uri TEXT NOT NULL,
                    metadata_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS resource_locks (
                    resource TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                    step_id TEXT NOT NULL, owner_id TEXT NOT NULL, expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS session_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL, event TEXT NOT NULL, step_id TEXT,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_session_events ON session_events(session_id, id);
                CREATE TABLE IF NOT EXISTS workflows (
                    name TEXT NOT NULL, version INTEGER NOT NULL, definition_json TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1, archived INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL, PRIMARY KEY (name, version)
                );
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                    version INTEGER NOT NULL, session_id TEXT NOT NULL, inputs_json TEXT NOT NULL,
                    status TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT
                );
                """
            )
            existing = {row["name"] for row in self._connection.execute("PRAGMA table_info(sessions)")}
            for name, sql_type in self.SESSION_COLUMNS.items():
                if name not in existing:
                    self._connection.execute(f"ALTER TABLE sessions ADD COLUMN {name} {sql_type}")
            workflow_columns = {
                row["name"] for row in self._connection.execute("PRAGMA table_info(workflows)")
            }
            if "archived" not in workflow_columns:
                self._connection.execute("ALTER TABLE workflows ADD COLUMN archived INTEGER NOT NULL DEFAULT 0")

    def create(self, session: Session) -> Session:
        session.updated_at = utc_now()
        with self._lock, self._connection:
            self._insert_session(session)
            self._insert_plan(session, "initial plan")
            self._sync_steps(session)
            self._append(session.id, "session_created", None, {"goal": session.goal})
        return session

    def save(self, session: Session, event: str | None = None, step_id: str | None = None,
             payload: dict[str, Any] | None = None) -> Session:
        session.updated_at = utc_now()
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """UPDATE sessions SET goal=?, status=?, mode=?, current_step_id=?,
                   pending_confirmation_json=?, error=?, updated_at=?, action_count=?,
                   replan_count=?, max_replans=?, max_duration_seconds=?, started_at=?,
                   approved_plan_hash=?, owner_id=?, lease_expires_at=? WHERE id=?""",
                self._session_update_values(session),
            )
            if not cursor.rowcount:
                raise KeyError(session.id)
            self._sync_steps(session)
            if event:
                self._append(session.id, event, step_id, payload or {})
        return session

    def save_plan(self, session: Session, reason: str) -> Session:
        session.updated_at = utc_now()
        with self._lock, self._connection:
            self._insert_plan(session, reason)
            self._sync_steps(session, remove_obsolete=True)
            self._append(session.id, "plan_revised", None, {
                "version": session.plan.version, "reason": reason,
            })
            self._connection.execute(
                """UPDATE sessions SET status=?, current_step_id=NULL,
                   pending_confirmation_json=NULL, updated_at=?, replan_count=?,
                   approved_plan_hash=NULL WHERE id=?""",
                (session.status.value, session.updated_at, session.replan_count, session.id),
            )
        return session

    def get(self, session_id: str) -> Session:
        with self._lock:
            row = self._connection.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
            if not row:
                raise KeyError(session_id)
            plan_row = self._connection.execute(
                "SELECT plan_json FROM plan_versions WHERE session_id=? ORDER BY version DESC LIMIT 1",
                (session_id,),
            ).fetchone()
            runtime_rows = self._connection.execute(
                "SELECT step_id, runtime_json FROM steps WHERE session_id=?", (session_id,)
            ).fetchall()
        plan = Plan.from_dict(self._loads(plan_row["plan_json"]))
        runtime = {item["step_id"]: self._loads(item["runtime_json"]) for item in runtime_rows}
        for step in plan.steps:
            for key, value in runtime.get(step.id, {}).items():
                if key == "status":
                    value = StepStatus(value)
                setattr(step, key, value)
        value = dict(row)
        value["pending_confirmation"] = self._loads(value.pop("pending_confirmation_json"))
        value["plan"] = plan.to_dict()
        return Session.from_dict(value)

    def list(self, statuses: tuple[str, ...] | None = None) -> list[Session]:
        query, parameters = "SELECT id FROM sessions", ()
        if statuses:
            placeholders = ",".join("?" for _ in statuses)
            query += f" WHERE status IN ({placeholders})"
            parameters = statuses
        query += " ORDER BY updated_at, id"
        with self._lock:
            ids = [row["id"] for row in self._connection.execute(query, parameters)]
        return [self.get(item) for item in ids]

    def events(self, session_id: str, after_id: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM session_events WHERE session_id=? AND id>? ORDER BY id",
                (session_id, after_id),
            ).fetchall()
        return [{**dict(row), "payload": self._loads(row["payload_json"])} for row in rows]

    def begin_attempt(self, session_id: str, step_id: str, attempt: int):
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT OR REPLACE INTO step_attempts
                   (session_id, step_id, attempt, status, started_at) VALUES (?, ?, ?, ?, ?)""",
                (session_id, step_id, attempt, "running", utc_now()),
            )

    def finish_attempt(self, session_id: str, step_id: str, attempt: int,
                       status: str, error_code: str | None = None, error: str | None = None):
        with self._lock, self._connection:
            self._connection.execute(
                """UPDATE step_attempts SET status=?, finished_at=?, error_code=?, error=?
                   WHERE session_id=? AND step_id=? AND attempt=?""",
                (status, utc_now(), error_code, error, session_id, step_id, attempt),
            )

    def start_tool_call(self, call_id: str, session_id: str, step_id: str, attempt: int,
                        action: str, arguments: dict[str, Any], idempotency_key: str | None):
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO tool_calls
                   (id, session_id, step_id, attempt, action, arguments_json, idempotency_key,
                    status, started_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'running', ?)""",
                (call_id, session_id, step_id, attempt, action, self._json(arguments),
                 idempotency_key, utc_now()),
            )

    def finish_tool_call(self, call_id: str, status: str, result: dict[str, Any]):
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE tool_calls SET status=?, result_json=?, finished_at=? WHERE id=?",
                (status, self._json(result, redact_value=True), utc_now(), call_id),
            )

    def completed_tool_call(self, idempotency_key: str | None) -> dict[str, Any] | None:
        if not idempotency_key:
            return None
        with self._lock:
            row = self._connection.execute(
                """SELECT result_json FROM tool_calls
                   WHERE idempotency_key=? AND status='succeeded' LIMIT 1""",
                (idempotency_key,),
            ).fetchone()
        return self._loads(row["result_json"]) if row else None

    def add_verification(self, session_id: str, step_id: str, attempt: int,
                         kind: str, success: bool, details: dict[str, Any]):
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO verifications
                   (session_id, step_id, attempt, kind, success, details_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_id, step_id, attempt, kind, int(success),
                 self._json(details, redact_value=True), utc_now()),
            )

    def put_approval(self, confirmation_id: str, session_id: str, step_id: str | None,
                     plan_version: int, scope_hash: str, request: dict[str, Any]):
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO approvals
                   (confirmation_id, session_id, step_id, plan_version, scope_hash,
                    request_json, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
                (confirmation_id, session_id, step_id, plan_version, scope_hash,
                 self._json(request, redact_value=True), utc_now()),
            )

    def answer_approval(self, confirmation_id: str, answer: dict[str, Any], status: str):
        with self._lock, self._connection:
            self._connection.execute(
                """UPDATE approvals SET answer_json=?, status=?, answered_at=?
                   WHERE confirmation_id=? AND status='pending'""",
                (self._json(answer, redact_value=True), status, utc_now(), confirmation_id),
            )

    def acquire_lease(self, session_id: str, owner_id: str, seconds: float = 30.0) -> bool:
        now = datetime.now(UTC)
        expires = (now + timedelta(seconds=seconds)).isoformat()
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT owner_id, lease_expires_at FROM sessions WHERE id=?", (session_id,)
            ).fetchone()
            if not row:
                raise KeyError(session_id)
            active = row["lease_expires_at"] and datetime.fromisoformat(row["lease_expires_at"]) > now
            if active and row["owner_id"] != owner_id:
                return False
            self._connection.execute(
                "UPDATE sessions SET owner_id=?, lease_expires_at=? WHERE id=?",
                (owner_id, expires, session_id),
            )
        return True

    def release_lease(self, session_id: str, owner_id: str):
        with self._lock, self._connection:
            self._connection.execute(
                """UPDATE sessions SET owner_id=NULL, lease_expires_at=NULL
                   WHERE id=? AND owner_id=?""", (session_id, owner_id)
            )

    def acquire_resources(self, resources: tuple[str, ...], session_id: str,
                          step_id: str, owner_id: str, seconds: float = 60.0) -> bool:
        expires = (datetime.now(UTC) + timedelta(seconds=seconds)).isoformat()
        with self._lock, self._connection:
            self._connection.execute("DELETE FROM resource_locks WHERE expires_at <= ?", (utc_now(),))
            if resources:
                placeholders = ",".join("?" for _ in resources)
                row = self._connection.execute(
                    f"SELECT resource FROM resource_locks WHERE resource IN ({placeholders})", resources
                ).fetchone()
                if row:
                    return False
            for resource in resources:
                self._connection.execute(
                    """INSERT INTO resource_locks
                       (resource, session_id, step_id, owner_id, expires_at) VALUES (?, ?, ?, ?, ?)""",
                    (resource, session_id, step_id, owner_id, expires),
                )
        return True

    def release_resources(self, session_id: str, step_id: str, owner_id: str):
        with self._lock, self._connection:
            self._connection.execute(
                "DELETE FROM resource_locks WHERE session_id=? AND step_id=? AND owner_id=?",
                (session_id, step_id, owner_id),
            )

    def put_workflow(self, name: str, version: int, definition: dict[str, Any]):
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT INTO workflows
                   (name, version, definition_json, created_at) VALUES (?, ?, ?, ?)""",
                (name, version, self._json(definition), utc_now()),
            )

    def get_workflow(self, name: str, version: int | None = None,
                     include_archived: bool = False) -> dict[str, Any]:
        query = "SELECT definition_json FROM workflows WHERE name=? AND enabled=1"
        parameters: tuple[Any, ...] = (name,)
        if not include_archived:
            query += " AND archived=0"
        if version is not None:
            query += " AND version=?"
            parameters += (version,)
        query += " ORDER BY version DESC LIMIT 1"
        with self._lock:
            row = self._connection.execute(query, parameters).fetchone()
        if not row:
            raise KeyError(name)
        return self._loads(row["definition_json"])

    def set_workflow_state(self, name: str, enabled: bool | None = None,
                           archived: bool | None = None):
        assignments, values = [], []
        if enabled is not None:
            assignments.append("enabled=?")
            values.append(int(enabled))
        if archived is not None:
            assignments.append("archived=?")
            values.append(int(archived))
        if not assignments:
            return
        with self._lock, self._connection:
            self._connection.execute(
                f"UPDATE workflows SET {', '.join(assignments)} WHERE name=?", (*values, name)
            )

    def delete_workflow(self, name: str):
        with self._lock, self._connection:
            self._connection.execute("DELETE FROM workflows WHERE name=?", (name,))

    def list_workflows(self, include_archived: bool = False) -> list[dict[str, Any]]:
        where = "" if include_archived else "WHERE archived=0"
        with self._lock:
            rows = self._connection.execute(
                f"""SELECT name, MAX(version) AS version, MIN(enabled) AS enabled,
                    MAX(archived) AS archived FROM workflows {where}
                    GROUP BY name ORDER BY name"""
            ).fetchall()
        return [dict(row) for row in rows]

    def start_workflow_run(self, name: str, version: int, session_id: str, inputs: dict[str, Any]) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """INSERT INTO workflow_runs
                   (name, version, session_id, inputs_json, status, started_at)
                   VALUES (?, ?, ?, ?, 'running', ?)""",
                (name, version, session_id, self._json(inputs, redact_value=True), utc_now()),
            )
            return int(cursor.lastrowid)

    def close(self):
        with self._lock:
            self._connection.close()

    def _insert_session(self, session: Session):
        self._connection.execute(
            """INSERT INTO sessions
               (id, goal, status, mode, current_step_id, pending_confirmation_json,
                error, created_at, updated_at, action_count, replan_count, max_replans,
                max_duration_seconds, started_at, approved_plan_hash, owner_id, lease_expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session.id, session.goal, session.status.value, session.mode.value,
             session.current_step_id, None, session.error, session.created_at,
             session.updated_at, session.action_count, session.replan_count,
             session.max_replans, session.max_duration_seconds, session.started_at,
             session.approved_plan_hash, session.owner_id, session.lease_expires_at),
        )

    def _session_update_values(self, session: Session) -> tuple[Any, ...]:
        pending = self._json(session.pending_confirmation, redact_value=True) if session.pending_confirmation else None
        return (
            session.goal, session.status.value, session.mode.value, session.current_step_id,
            pending, session.error, session.updated_at, session.action_count,
            session.replan_count, session.max_replans, session.max_duration_seconds,
            session.started_at, session.approved_plan_hash, session.owner_id,
            session.lease_expires_at, session.id,
        )

    def _insert_plan(self, session: Session, reason: str):
        self._connection.execute(
            """INSERT INTO plan_versions
               (session_id, version, plan_json, reason, created_at) VALUES (?, ?, ?, ?, ?)""",
            (session.id, session.plan.version, self._json(session.plan.definition_dict()), reason, utc_now()),
        )

    def _sync_steps(self, session: Session, remove_obsolete: bool = False):
        ids = [step.id for step in session.plan.steps]
        if remove_obsolete:
            if ids:
                placeholders = ",".join("?" for _ in ids)
                self._connection.execute(
                    f"DELETE FROM steps WHERE session_id=? AND step_id NOT IN ({placeholders})",
                    (session.id, *ids),
                )
            else:
                self._connection.execute("DELETE FROM steps WHERE session_id=?", (session.id,))
        for step in session.plan.steps:
            runtime = step.runtime_dict()
            runtime["status"] = step.status.value
            self._connection.execute(
                """INSERT INTO steps
                   (session_id, step_id, plan_version, status, runtime_json, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(session_id, step_id) DO UPDATE SET
                   plan_version=excluded.plan_version, status=excluded.status,
                   runtime_json=excluded.runtime_json, updated_at=excluded.updated_at""",
                (session.id, step.id, session.plan.version, step.status.value,
                 self._json(runtime), utc_now()),
            )

    def _append(self, session_id: str, event: str, step_id: str | None, payload: dict[str, Any]):
        self._connection.execute(
            """INSERT INTO session_events
               (session_id, timestamp, event, step_id, payload_json) VALUES (?, ?, ?, ?, ?)""",
            (session_id, utc_now(), event, step_id, self._json(payload, redact_value=True)),
        )

    @staticmethod
    def _json(value: Any, redact_value: bool = False) -> str:
        return json.dumps(redact(value) if redact_value else value,
                          ensure_ascii=False, sort_keys=True, default=str)

    @staticmethod
    def _loads(value: str | None) -> Any:
        return json.loads(value) if value else None
