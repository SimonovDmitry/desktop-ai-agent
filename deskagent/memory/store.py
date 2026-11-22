"""Thread-safe, persistent JSON memory backed by SQLite.

All operations on one store are serialized. Separate stores/processes coordinate
through SQLite transactions and a busy timeout. Values must be JSON serializable;
serialization failures never change previously stored data.
"""

import json
import math
import sqlite3
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from time import time
from typing import Any


class MemoryStore:
    """Namespaced memory with optional expiry and atomic document replacement.

    Existing four-column databases are migrated in place. Explicit paths are
    honored: filesystem and database errors propagate instead of silently opening
    a different database. ``:memory:`` creates a private in-memory database.
    """

    def __init__(self, path="~/.deskagent/memory.sqlite", *, timeout: float = 5.0):
        self.lock = threading.RLock()
        self._closed = False
        target = str(path) if str(path) == ":memory:" else Path(path).expanduser()
        if isinstance(target, Path):
            target.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(target, timeout=timeout, check_same_thread=False)
        try:
            # Serialize schema inspection and migration across concurrent openers.
            with self.lock, self.connection:
                self.connection.execute("BEGIN IMMEDIATE")
                self.connection.execute(
                    "CREATE TABLE IF NOT EXISTS memory ("
                    "namespace TEXT, key TEXT, value TEXT, updated_at TEXT, "
                    "expires_at REAL, PRIMARY KEY(namespace,key))"
                )
                columns = {row[1] for row in self.connection.execute("PRAGMA table_info(memory)")}
                if "expires_at" not in columns:
                    self.connection.execute("ALTER TABLE memory ADD COLUMN expires_at REAL")
                self.connection.execute(
                    "CREATE INDEX IF NOT EXISTS memory_expiry ON memory(expires_at)"
                )
        except BaseException:
            self.connection.close()
            raise

    @contextmanager
    def _access(self, *, write=False):
        with self.lock:
            if self._closed:
                raise RuntimeError("MemoryStore is closed")
            if write:
                with self.connection:
                    self.connection.execute("BEGIN IMMEDIATE")
                    yield
            else:
                yield

    @staticmethod
    def _name(value, name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    @staticmethod
    def _integer(value, name, minimum=0):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")

    @staticmethod
    def _payload(value):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)

    def _put(self, namespace, key, payload, expires_at=None):
        self.connection.execute(
            "INSERT INTO memory(namespace,key,value,updated_at,expires_at) VALUES(?,?,?,?,?) "
            "ON CONFLICT(namespace,key) DO UPDATE SET value=excluded.value,"
            "updated_at=excluded.updated_at,expires_at=excluded.expires_at",
            (namespace, key, payload, datetime.now(UTC).isoformat(), expires_at),
        )

    def put(self, namespace: str, key: str, value: Any, *, ttl: float | None = None):
        """Upsert a JSON value. TTL is in seconds; zero expires immediately."""
        self._name(namespace, "namespace")
        self._name(key, "key")
        if ttl is not None and (
            isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or not math.isfinite(ttl) or ttl < 0
        ):
            raise ValueError("ttl must be a finite non-negative number")
        payload = self._payload(value)
        with self._access(write=True):
            self._put(namespace, key, payload, None if ttl is None else time() + ttl)

    def get(self, namespace: str, key: str, default=None):
        self._name(namespace, "namespace")
        self._name(key, "key")
        with self._access():
            row = self.connection.execute(
                "SELECT value FROM memory WHERE namespace=? AND key=? "
                "AND (expires_at IS NULL OR expires_at>?)", (namespace, key, time()),
            ).fetchone()
        return json.loads(row[0]) if row else default

    def search(self, query: str, namespace: str | None = None, limit=20):
        """Literal, Unicode case-insensitive substring search across keys and JSON.

        Empty queries list live entries. Results are newest first with stable
        namespace/key tie-breaking. No SQL wildcard or query syntax is interpreted.
        This scan favors portability and exact behavior over large-corpus ranking.
        """
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        if namespace is not None:
            self._name(namespace, "namespace")
        self._integer(limit, "limit")
        sql = "SELECT namespace,key,value,updated_at FROM memory WHERE (expires_at IS NULL OR expires_at>?)"
        params = [time()]
        if namespace is not None:
            sql += " AND namespace=?"
            params.append(namespace)
        sql += " ORDER BY updated_at DESC,namespace,key"
        needle = query.casefold()
        results = []
        with self._access():
            if limit == 0:
                return []
            cursor = self.connection.execute(sql, params)
            try:
                for ns, key, value, at in cursor:
                    if needle in key.casefold() or needle in value.casefold():
                        results.append({"namespace": ns, "key": key, "value": json.loads(value), "updated_at": at})
                        if len(results) == limit:
                            break
            finally:
                cursor.close()
        return results

    def delete(self, namespace: str, key: str) -> bool:
        """Delete one entry, including an expired entry; report whether it existed."""
        self._name(namespace, "namespace")
        self._name(key, "key")
        with self._access(write=True):
            return self.connection.execute(
                "DELETE FROM memory WHERE namespace=? AND key=?", (namespace, key)
            ).rowcount > 0

    def clear(self, namespace: str) -> int:
        """Delete a namespace and return the number of removed entries."""
        self._name(namespace, "namespace")
        with self._access(write=True):
            return self.connection.execute("DELETE FROM memory WHERE namespace=?", (namespace,)).rowcount

    def prune_expired(self) -> int:
        with self._access(write=True):
            return self.connection.execute("DELETE FROM memory WHERE expires_at<=?", (time(),)).rowcount

    def index_text(self, source: str, text: str, chunk_size=1200, *, overlap=0):
        """Atomically replace a source's chunks; empty text removes its index.

        Chunk sizes and overlap are measured in Unicode characters. Only keys
        generated for this exact source are replaced, including legacy chunks.
        """
        self._name(source, "source")
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        self._integer(chunk_size, "chunk_size", 1)
        self._integer(overlap, "overlap")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        with self._access(write=True):
            rows = self.connection.execute("SELECT key FROM memory WHERE namespace='documents'").fetchall()
            prefix = source + ":"
            keys = [(key,) for (key,) in rows if key.startswith(prefix) and key[len(prefix):].isdigit()]
            self.connection.executemany("DELETE FROM memory WHERE namespace='documents' AND key=?", keys)
            count = 0
            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                self._put("documents", f"{source}:{count}", self._payload({
                    "source": source, "chunk": count, "text": text[start:end],
                }))
                count += 1
                if end == len(text):
                    break
                start = end - overlap
            return count

    def index_file(self, path, chunk_size=1200, *, overlap=0):
        """Index UTF-8 text; decoding errors preserve the previous index."""
        target = Path(path).expanduser().resolve()
        return self.index_text(str(target), target.read_text(encoding="utf-8"), chunk_size, overlap=overlap)

    def close(self):
        """Close once; subsequent operations raise RuntimeError."""
        with self.lock:
            if not self._closed:
                self.connection.close()
                self._closed = True

    def __enter__(self):
        with self._access():
            return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
