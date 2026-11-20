"""Bounded project and Git primitives for code actions."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.privacy.guards import FilesystemGuard

MAX_FILES = 5000
MAX_FILE_BYTES = 2_000_000
MAX_OUTPUT = 200_000
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache",
             ".pytest_cache", "dist", "build", ".tox", ".idea"}
TEXT_SUFFIXES = {".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".json", ".toml", ".yaml",
                 ".yml", ".md", ".rst", ".txt", ".sh", ".bash", ".css", ".html", ".sql",
                 ".java", ".go", ".rs", ".c", ".h", ".cpp", ".hpp", ".swift", ".kt"}
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{4,64}$")


class CodeAction(Action):
    discoverable = False
    category = ActionCategory.CODE

    @staticmethod
    def run(operation):
        try:
            return ActionResult(True, operation())
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="CODE_ERROR")


def _guard(context):
    security = context.settings.security
    return FilesystemGuard(security.allowed_paths, security.blocked_paths)


def project_dir(context, value):
    project = Path(value).expanduser().resolve()
    if not project.is_dir():
        raise NotADirectoryError(project)
    decision = _guard(context).check("read_file", {"directory": str(project)})
    if not decision.allowed:
        raise PermissionError(decision.reason)
    return project


def safe_file(context, project, value, *, required=True):
    candidate = (project / value).resolve()
    if not candidate.is_relative_to(project):
        raise ValueError("File path is outside the project")
    decision = _guard(context).check("read_file", {"path": str(candidate)})
    if not decision.allowed:
        raise PermissionError(decision.reason)
    if required and not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def read_source(context, project, value):
    path = safe_file(context, project, value)
    if path.suffix.lower() not in TEXT_SUFFIXES:
        raise ValueError("Unsupported source file extension")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Source file exceeds 2 MB limit")
    return path, path.read_text(encoding="utf-8-sig")


def walk_sources(context, project):
    count = 0
    for root, dirs, files in os.walk(project, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS
                         if not (Path(root) / name).is_symlink())
        for name in sorted(files):
            path = Path(root) / name
            if path.is_symlink() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            count += 1
            if count > MAX_FILES:
                raise ValueError("Project exceeds 5000 source files")
            if not _guard(context).check("read_file", {"path": str(path)}).allowed:
                continue
            if path.stat().st_size <= MAX_FILE_BYTES:
                yield path


def git(project, *args, max_output=MAX_OUTPUT):
    command = ["git", "-C", str(project), "--no-pager", *args]
    result = subprocess.run(command, capture_output=True, text=True, timeout=25,
                            errors="replace")
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[:1000] or "Git command failed")
    return result.stdout[:max_output], len(result.stdout) > max_output


def git_names(context, project, *args):
    output, truncated = git(project, *args, "-z", max_output=2_000_000)
    if truncated:
        raise ValueError("Git file list exceeds processing limit")
    names, excluded = [], 0
    for name in output.split("\0"):
        if not name:
            continue
        try:
            safe_file(context, project, name, required=False)
        except (ValueError, PermissionError):
            excluded += 1
            continue
        names.append(name)
        if len(names) > MAX_FILES:
            raise ValueError("Git file list exceeds 5000 files")
    return names, excluded


def commit_id(value):
    if not isinstance(value, str) or not COMMIT_RE.fullmatch(value):
        raise ValueError("Commit must be a hexadecimal object id")
    return value
