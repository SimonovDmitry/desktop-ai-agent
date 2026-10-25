from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deskagent.safety.confirmation import redact


@dataclass(frozen=True)
class AuditRecord:
    event: str
    action: str
    parameters: dict[str, Any]
    risk: str
    decision: str
    thread_id: str | None = None
    tool_call_id: str | None = None
    confirmation_id: str | None = None
    result: dict[str, Any] | None = None
    timestamp: str | None = None


class AuditLog:
    """Append-only SQLite audit log with redaction at the storage boundary."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        try:
            self.path.chmod(0o600)
        except OSError:
            pass
        self._lock = threading.RLock()
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event TEXT NOT NULL,
                thread_id TEXT,
                tool_call_id TEXT,
                action TEXT NOT NULL,
                parameters_json TEXT NOT NULL,
                risk TEXT NOT NULL,
                decision TEXT NOT NULL,
                confirmation_id TEXT,
                result_json TEXT
            )
        """)
        self._connection.execute("CREATE INDEX IF NOT EXISTS idx_audit_thread_time ON audit_logs(thread_id, timestamp)")
        self._connection.commit()

    def append(self, record: AuditRecord) -> int:
        timestamp = record.timestamp or datetime.now(timezone.utc).isoformat()
        parameters = json.dumps(redact(record.parameters), ensure_ascii=False, sort_keys=True, default=str)
        result = None if record.result is None else json.dumps(redact(record.result), ensure_ascii=False, sort_keys=True, default=str)
        with self._lock:
            cursor = self._connection.execute(
                """INSERT INTO audit_logs
                   (timestamp, event, thread_id, tool_call_id, action, parameters_json,
                    risk, decision, confirmation_id, result_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (timestamp, record.event, record.thread_id, record.tool_call_id, record.action,
                 parameters, record.risk, record.decision, record.confirmation_id, result),
            )
            self._connection.commit()
            return int(cursor.lastrowid)

    def list(self, thread_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 1000))
        query = "SELECT * FROM audit_logs"
        parameters: tuple[Any, ...] = ()
        if thread_id is not None:
            query += " WHERE thread_id = ?"
            parameters = (thread_id,)
        query += " ORDER BY id DESC LIMIT ?"
        with self._lock:
            cursor = self._connection.execute(query, (*parameters, limit))
            columns = [item[0] for item in cursor.description]
            rows = []
            for values in cursor.fetchall():
                row = dict(zip(columns, values))
                row["parameters"] = json.loads(row.pop("parameters_json"))
                raw_result = row.pop("result_json")
                row["result"] = json.loads(raw_result) if raw_result else None
                rows.append(row)
            return rows

    def close(self):
        with self._lock:
            self._connection.close()
