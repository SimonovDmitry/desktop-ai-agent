import os
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def create_checkpointer(path: str | Path | None = None) -> SqliteSaver:
    target = Path(path or os.getenv("DESKAGENT_CHECKPOINTS", "~/.deskagent/checkpoints.sqlite")).expanduser()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(target, check_same_thread=False)
    except OSError:
        local = Path(".deskagent").resolve()
        local.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(local / target.name, check_same_thread=False)
    return SqliteSaver(connection)
