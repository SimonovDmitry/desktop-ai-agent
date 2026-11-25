import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from deskagent.memory import MemoryStore


def test_persistence_and_namespace_isolation(tmp_path):
    path = tmp_path / "nested" / "memory.sqlite"
    with MemoryStore(path) as store:
        store.put("a", "key", {"text": "Привет", "items": [1, None, True]})
        store.put("b", "key", 42)
    with MemoryStore(path) as store:
        assert store.get("a", "key")["text"] == "Привет"
        assert store.get("b", "key") == 42
        assert store.get("missing", "key", "fallback") == "fallback"
        assert store.clear("a") == 1
        assert store.get("b", "key") == 42
        assert store.delete("b", "key")
        assert not store.delete("b", "key")


def test_migrates_legacy_database(tmp_path):
    path = tmp_path / "old.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE memory(namespace TEXT,key TEXT,value TEXT,updated_at TEXT,"
                           "PRIMARY KEY(namespace,key))")
        connection.execute("INSERT INTO memory VALUES('old','key','42','2025-01-01')")
    for _ in range(2):
        with MemoryStore(path) as store:
            assert store.get("old", "key") == 42
            store.put("new", "key", "value", ttl=60)


def test_expiry_and_overwrite(monkeypatch):
    monkeypatch.setattr("deskagent.memory.store.time", lambda: 100)
    with MemoryStore(":memory:") as store:
        store.put("n", "k", 1, ttl=10)
        monkeypatch.setattr("deskagent.memory.store.time", lambda: 110)
        assert store.get("n", "k") is None
        assert store.search("") == []
        assert store.prune_expired() == 1
        store.put("n", "k", 2, ttl=0)
        store.put("n", "k", 3)
        assert store.get("n", "k") == 3
        assert store.prune_expired() == 0


def test_literal_unicode_search_and_limits():
    with MemoryStore(":memory:") as store:
        store.put("n", "Русский", "100%_value")
        store.put("other", "plain", "anything")
        assert len(store.search("%_")) == 1
        assert len(store.search("РУССКИЙ", "n")) == 1
        assert len(store.search("", limit=1)) == 1
        assert store.search("", limit=0) == []
        for limit in (-1, True, 1.5):
            with pytest.raises(ValueError):
                store.search("", limit=limit)


def test_invalid_values_do_not_replace_memory():
    with MemoryStore(":memory:") as store:
        store.put("n", "k", "original")
        for value in (object(), float("nan"), {"set"}):
            with pytest.raises((ValueError, TypeError)):
                store.put("n", "k", value)
        for ttl in (-1, float("inf"), float("nan"), True, "10"):
            with pytest.raises(ValueError):
                store.put("n", "k", "bad", ttl=ttl)
        assert store.get("n", "k") == "original"
        with pytest.raises(ValueError):
            store.put("", "k", 1)


def test_reindex_overlap_and_source_isolation():
    with MemoryStore(":memory:") as store:
        assert store.index_text("a", "abcdefghij", 4, overlap=2) == 4
        assert store.get("documents", "a:1")["text"] == "cdef"
        store.index_text("a:child", "keep")
        store.index_text("a%", "keep too")
        assert store.index_text("a", "new") == 1
        assert store.get("documents", "a:1") is None
        assert store.index_text("a", "") == 0
        assert len(store.search("", "documents")) == 2
        for size, overlap in ((0, 0), (4, 4), (4, -1), (True, 0)):
            with pytest.raises(ValueError):
                store.index_text("a", "bad", size, overlap=overlap)


def test_index_rollback_on_write_failure(monkeypatch):
    with MemoryStore(":memory:") as store:
        store.index_text("source", "original")
        original = store._put

        def fail(namespace, key, payload, expires_at=None):
            original(namespace, key, payload, expires_at)
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(store, "_put", fail)
        with pytest.raises(RuntimeError, match="simulated"):
            store.index_text("source", "replacement", 3)
        assert store.get("documents", "source:0")["text"] == "original"
        assert len(store.search("", "documents")) == 1


def test_invalid_file_preserves_index(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("original", encoding="utf-8")
    with MemoryStore(":memory:") as store:
        store.index_file(path)
        path.write_bytes(b"\xff")
        with pytest.raises(UnicodeDecodeError):
            store.index_file(path)
        assert store.get("documents", f"{path}:0")["text"] == "original"


def test_concurrent_connections_and_threads(tmp_path):
    path = tmp_path / "shared.sqlite"

    def worker(index):
        with MemoryStore(path) as store:
            for i in range(15):
                store.put("n", f"{index}:{i}", i)
                assert store.get("n", f"{index}:{i}") == i
                store.search("", limit=2)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(worker, range(4)))
    with MemoryStore(path) as store:
        assert len(store.search("", limit=100)) == 60
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda i: store.put("shared", str(i), i), range(40)))
        assert len(store.search("", "shared", limit=100)) == 40


def test_close_and_compatibility():
    from deskagent.agent.capabilities.memory import MemoryStore as LegacyStore
    assert LegacyStore is MemoryStore
    store = MemoryStore(":memory:")
    store.close()
    store.close()
    with pytest.raises(RuntimeError, match="closed"):
        store.get("n", "k")
