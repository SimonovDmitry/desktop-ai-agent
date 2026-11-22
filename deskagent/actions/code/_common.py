"""Action wrappers for portable platform operations."""
from __future__ import annotations

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.platform.common import code as portable
from deskagent.platform.common.code import (  # noqa: F401
    MAX_FILES,
    MAX_FILE_BYTES,
    MAX_OUTPUT,
    SKIP_DIRS,
    TEXT_SUFFIXES,
    COMMIT_RE,
    _guard,
    commit_id,
)


class CodeAction(Action):
    discoverable = False
    category = ActionCategory.CODE

    @staticmethod
    def run(operation):
        try:
            return ActionResult(True, operation())
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="CODE_ERROR")


def project_dir(context, value):
    service = getattr(getattr(context, "services", None), "code", None)
    return (service or portable.CodeService()).project_dir(context, value)


def safe_file(context, project, value, *, required=True):
    service = getattr(getattr(context, "services", None), "code", None)
    return (service or portable.CodeService()).safe_file(context, project, value, required=required)


def read_source(context, project, value):
    service = getattr(getattr(context, "services", None), "code", None)
    return (service or portable.CodeService()).read_source(context, project, value)


def walk_sources(context, project):
    service = getattr(getattr(context, "services", None), "code", None)
    return (service or portable.CodeService()).walk_sources(context, project)


def git_names(context, project, *args):
    service = getattr(getattr(context, "services", None), "code", None)
    return (service or portable.CodeService()).git_names(context, project, *args)


def git(context, project, *args, max_output=MAX_OUTPUT):
    service = getattr(getattr(context, "services", None), "code", None)
    return (service or portable.CodeService()).git(project, *args, max_output=max_output)
