import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any


class MemoryStore:
    def __init__(self, path="~/.deskagent/memory.sqlite"):
        target = Path(path).expanduser()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(target, check_same_thread=False)
        except OSError:
            local = Path(".deskagent").resolve()
            local.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(local / target.name, check_same_thread=False)
        self.lock = threading.RLock()
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS memory (namespace TEXT, key TEXT, value TEXT, updated_at TEXT, PRIMARY KEY(namespace,key))"
        )
        self.connection.commit()

    def put(self, namespace: str, key: str, value: Any):
        payload = json.dumps(value, ensure_ascii=False, default=str)
        with self.lock:
            self.connection.execute(
                "INSERT INTO memory VALUES(?,?,?,?) ON CONFLICT(namespace,key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                (namespace, key, payload, datetime.now().astimezone().isoformat()),
            )
            self.connection.commit()

    def get(self, namespace: str, key: str, default=None):
        row = self.connection.execute(
            "SELECT value FROM memory WHERE namespace=? AND key=?", (namespace, key),
        ).fetchone()
        return json.loads(row[0]) if row else default

    def search(self, query: str, namespace: str | None = None, limit=20):
        sql, params = "SELECT namespace,key,value,updated_at FROM memory WHERE value LIKE ?", [f"%{query}%"]
        if namespace:
            sql, params = f"{sql} AND namespace=?", [*params, namespace]
        rows = self.connection.execute(f"{sql} ORDER BY updated_at DESC LIMIT ?", [*params, limit]).fetchall()
        return [{"namespace": ns, "key": key, "value": json.loads(value), "updated_at": at} for ns, key, value, at in rows]

    def index_text(self, source: str, text: str, chunk_size=1200):
        chunks = [text[index:index + chunk_size] for index in range(0, len(text), chunk_size)]
        for index, chunk in enumerate(chunks):
            self.put("documents", f"{source}:{index}", {"source": source, "chunk": index, "text": chunk})
        return len(chunks)

    def index_file(self, path, chunk_size=1200):
        source = str(Path(path).expanduser().resolve())
        return self.index_text(source, Path(source).read_text(encoding="utf-8", errors="ignore"), chunk_size)
