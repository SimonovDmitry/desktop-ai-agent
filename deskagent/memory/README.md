# Agent memory

`deskagent.memory.MemoryStore` stores JSON values under `(namespace, key)` in
SQLite. The former `deskagent.agent.capabilities.memory` and
`deskagent.agent.memory` imports remain supported.

```python
from deskagent.memory import MemoryStore

with MemoryStore("~/.deskagent/memory.sqlite") as memory:
    memory.put("preferences", "language", "ru")
    memory.put("session", "active_task", {"id": 123}, ttl=3600)
    language = memory.get("preferences", "language", default="en")
    memory.index_text("notes.txt", "Some useful notes", chunk_size=1200, overlap=100)
    matches = memory.search("useful", namespace="documents", limit=10)
    memory.delete("session", "active_task")
    memory.prune_expired()
```

## Contracts

- Values use strict JSON serialization: unsupported objects and non-finite
  numbers raise before writing. There is no implicit conversion to strings.
- `get` returns the provided default for missing or expired entries. A stored
  JSON `null` returns `None`. Upserts replace the value and reset its TTL.
- TTL accepts finite non-negative seconds; zero expires immediately. Reads hide
  expired data; `prune_expired` physically removes it and returns the count.
- `search` matches literal case-insensitive substrings in keys and serialized
  JSON values, using Unicode case folding. `%` and `_` are ordinary characters.
  It returns dictionaries with `namespace`, `key`, `value`, and `updated_at`.
  Empty queries list entries. Results are newest first, with namespace/key ties.
  This is a linear scan within the chosen namespace, not semantic or ranked
  retrieval; bound corpus size and use namespaces for large datasets.
- `delete` returns whether a row existed, even if expired. `clear(namespace)`
  removes only that namespace and returns its row count. Both are permanent.
- `index_text` replaces all generated numeric chunk keys for the exact source in
  one transaction. Shorter or empty replacements remove obsolete chunks. A
  failed write restores the previous index. The `documents` namespace is reserved
  for indexed chunks, keyed as `source:chunk_number`.
- Chunk size and overlap count Unicode characters, not tokens or bytes. Overlap
  must be smaller than chunk size. There is no trailing overlap-only chunk.
- `index_file` resolves the path and strictly reads UTF-8 before changing memory.
  Missing files and decoding errors preserve the previous index. It reads the
  whole file, so callers should limit input file size.

## Persistence and lifecycle

Existing four-column memory tables receive an additive `expires_at` migration;
existing values are retained and do not expire. Initialization and writes use
SQLite immediate transactions, with a configurable connection `timeout` (default
five seconds) for competing writers. One store serializes reads and writes with
an `RLock`; independent stores and processes coordinate through SQLite locking.
Do not use the exposed `connection` directly during concurrent operations.

Use the context manager or call `close()` explicitly. Closing is idempotent;
further operations raise `RuntimeError`. `:memory:` is supported for temporary
stores. Filesystem, decoding, malformed stored JSON, and SQLite errors propagate
so callers can handle failures. Paths never silently fall back to another file.
The database contains plaintext JSON; filesystem access and retention are the
caller's responsibility.
