import os
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def create_checkpointer(path: str | Path | None = None) -> SqliteSaver:
    target = Path(path or os.getenv("DESKAGENT_CHECKPOINTS", "~/.deskagent/checkpoints.sqlite")).expanduser()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(target, check_same_thread=False)
        _restrict_permissions(target)
    except OSError:
        local = Path(".deskagent").resolve()
        local.mkdir(parents=True, exist_ok=True)
        target = local / target.name
        connection = sqlite3.connect(target, check_same_thread=False)
        _restrict_permissions(target)
    return SqliteSaver(connection)


def _restrict_permissions(path: Path):
    try:
        path.chmod(0o600)
    except OSError:
        # Some filesystems do not expose POSIX permissions. The policy layer
        # remains usable, while deployment diagnostics can report this later.
        pass
