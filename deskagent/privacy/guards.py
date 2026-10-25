from __future__ import annotations

import re
import shlex
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    reason: str | None = None
    code: str | None = None


class FilesystemGuard:
    """Resolve paths before comparing them, including non-existing targets."""

    PATH_KEYS = frozenset({
        "path", "file", "filename", "directory", "folder", "source",
        "destination", "target", "output", "input_path",
    })
    MUTATION_TOKENS = frozenset({
        "write", "create", "delete", "remove", "trash", "move", "rename",
        "copy", "duplicate", "extract", "compress", "archive", "chmod",
        "permission", "link", "save", "replace", "overwrite",
    })
    SECRET_NAMES = frozenset({
        ".npmrc", ".pypirc", ".netrc", ".git-credentials", "credentials",
        "credentials.json", "service-account.json", "id_rsa", "id_ed25519",
    })

    def __init__(self, allowed_paths: Iterable[str] = (), blocked_paths: Iterable[str] = ()):
        self.allowed_paths = tuple(self._resolve(path) for path in allowed_paths)
        self.blocked_paths = tuple(self._resolve(path) for path in blocked_paths)

    def check(self, action_name: str, parameters: dict[str, Any]) -> GuardResult:
        paths = tuple(self.paths(parameters))
        for path in paths:
            if self._is_sensitive(path):
                return GuardResult(False, f"Sensitive path is blocked: {path}", "SENSITIVE_PATH")
            if any(self._inside(path, root) for root in self.blocked_paths):
                return GuardResult(False, f"Path is blocked by policy: {path}", "BLOCKED_PATH")

        if paths and self._is_mutation(action_name) and self.allowed_paths:
            outside = next(
                (path for path in paths if not any(self._inside(path, root) for root in self.allowed_paths)),
                None,
            )
            if outside is not None:
                return GuardResult(False, f"Write target is outside allowed directories: {outside}", "PATH_NOT_ALLOWED")
        return GuardResult(True)

    def paths(self, value: Any, key: str = ""):
        if isinstance(value, dict):
            for child_key, child in value.items():
                yield from self.paths(child, str(child_key).casefold())
        elif isinstance(value, (list, tuple)):
            for child in value:
                yield from self.paths(child, key)
        elif isinstance(value, (str, os.PathLike)) and self._is_path_key(key):
            yield self._resolve(value)

    @classmethod
    def _is_path_key(cls, key: str) -> bool:
        return key in cls.PATH_KEYS or key.endswith("_path") or key.endswith("_file") or key.endswith("_dir")

    @classmethod
    def _is_mutation(cls, action_name: str) -> bool:
        name = action_name.casefold()
        return any(token in name for token in cls.MUTATION_TOKENS)

    @classmethod
    def _is_sensitive(cls, path: Path) -> bool:
        parts = tuple(part.casefold() for part in path.parts)
        name = path.name.casefold()
        if name == ".env" or name.startswith(".env.") or name in cls.SECRET_NAMES:
            return True
        if ".aws" in parts and name in {"credentials", "config"}:
            return True
        return any(part in {".ssh", ".gnupg", "keychains"} for part in parts)

    @staticmethod
    def _resolve(value: str | Path) -> Path:
        return Path(value).expanduser().resolve(strict=False)

    @staticmethod
    def _inside(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False


class ShellGuard:
    """Reject shell syntax that turns a command into an arbitrary program."""

    SHELL_NAMES = frozenset({
        "shell", "command", "terminal", "subprocess", "execute_process",
        "run_command", "run_shell", "execute_shell",
    })
    COMMAND_KEYS = ("command", "cmd", "script", "shell")
    CRITICAL_PATTERNS = (
        re.compile(r"(^|\s)(sudo|su)\b", re.I),
        re.compile(r"\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+)*(?:/|~|\$HOME)(?:\s|$)", re.I),
        re.compile(r"\b(curl|wget)\b[^\n]*(\||&&|;)\s*(sh|bash|zsh|python)\b", re.I),
        re.compile(r"\b(mkfs|diskutil\s+erase|dd\s+if=)\b", re.I),
    )
    META_PATTERN = re.compile(r"(?:\||&&|\|\||;|`|\$\(|>|<|\n)")

    def __init__(self, enabled: bool = False, allowed_commands: Iterable[str] = (), allow_metacharacters=False):
        self.enabled = enabled
        self.allowed_commands = frozenset(allowed_commands)
        self.allow_metacharacters = allow_metacharacters

    @classmethod
    def is_shell_action(cls, action_name: str) -> bool:
        name = action_name.casefold()
        return any(token in name for token in cls.SHELL_NAMES)

    def check(self, action_name: str, parameters: dict[str, Any]) -> GuardResult:
        if not self.is_shell_action(action_name):
            return GuardResult(True)
        if not self.enabled:
            return GuardResult(False, "Arbitrary shell execution is disabled", "SHELL_DISABLED")
        command = next((parameters.get(key) for key in self.COMMAND_KEYS if parameters.get(key)), "")
        if not isinstance(command, str) or not command.strip():
            return GuardResult(False, "Shell command is missing", "SHELL_COMMAND_MISSING")
        if any(pattern.search(command) for pattern in self.CRITICAL_PATTERNS):
            return GuardResult(False, "Destructive or piped remote shell command is prohibited", "SHELL_PROHIBITED")
        if not self.allow_metacharacters and self.META_PATTERN.search(command):
            return GuardResult(False, "Shell operators are prohibited; use a structured action", "SHELL_OPERATORS_BLOCKED")
        try:
            executable = Path(shlex.split(command)[0]).name
        except (ValueError, IndexError):
            return GuardResult(False, "Shell command cannot be parsed safely", "SHELL_PARSE_ERROR")
        if self.allowed_commands and executable not in self.allowed_commands:
            return GuardResult(False, f"Shell command is not allowlisted: {executable}", "SHELL_COMMAND_NOT_ALLOWED")
        return GuardResult(True)
