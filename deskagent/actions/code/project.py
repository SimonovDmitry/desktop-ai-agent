from __future__ import annotations

import subprocess

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.privacy.guards import FilesystemGuard
from deskagent.platform.common.code import CodeService
from deskagent.platform.common.code_project import _project


def _service(context):
    return getattr(getattr(context, "services", None), "code", None) or CodeService()


def _git(context, project, *args):
    return _service(context).git_output(project, *args)


DIRECTORY = {"directory": {"type": "string", "required": True}}


class GetGitStatus(Action):
    name = "get_git_status"
    description = "Read the branch and changed files in a local Git worktree"
    category = ActionCategory.CODE
    parameters_schema = DIRECTORY

    def execute(self, context, parameters):
        try:
            project = _project(parameters)
            return ActionResult(True, {
                "directory": str(project), **_git(context, project, "status", "--short", "--branch"),
            })
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="GIT_ERROR")


class ShowGitDiff(Action):
    name = "show_git_diff"
    description = "Read a bounded working-tree or staged Git diff without external diff commands"
    category = ActionCategory.CODE
    parameters_schema = {
        **DIRECTORY,
        "path": {"type": "string", "required": False},
        "staged": {"type": "boolean", "required": False, "default": False},
    }

    def execute(self, context, parameters):
        try:
            project = _project(parameters)
            args = ["diff", "--no-ext-diff", "--no-color"]
            if parameters.get("staged"):
                args.append("--cached")
            guard = FilesystemGuard(
                context.settings.security.allowed_paths, context.settings.security.blocked_paths
            )
            if parameters.get("path"):
                target = (project / parameters["path"]).resolve()
                if not target.is_relative_to(project):
                    raise ValueError("Diff path is outside the project")
                paths = [str(target.relative_to(project))]
            else:
                names = _git(context, project, *args, "--name-only", "-z")["output"]
                paths = [name for name in names.split("\0") if name]
            safe_paths, excluded = [], 0
            for name in paths:
                path = (project / name).resolve()
                if not path.is_relative_to(project):
                    continue
                if guard.check("read_file", {"path": str(path)}).allowed:
                    safe_paths.append(name)
                else:
                    excluded += 1
            if parameters.get("path") and not safe_paths:
                raise PermissionError("Diff path is sensitive or blocked")
            if not safe_paths:
                return ActionResult(True, {
                    "directory": str(project), "output": "", "truncated": False,
                    "excluded_sensitive_files": excluded,
                })
            args += ["--", *safe_paths]
            return ActionResult(True, {
                "directory": str(project), **_git(context, project, *args), "excluded_sensitive_files": excluded,
            })
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="GIT_ERROR")


class RunProjectTests(Action):
    name = "run_project_tests"
    description = "Run pytest in an allowed project directory and save a bounded result report"
    category = ActionCategory.CODE
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {
        **DIRECTORY,
        "target": {"type": "string", "required": False},
        "timeout": {"type": "integer", "required": False, "default": 120, "minimum": 1, "maximum": 300},
    }

    def execute(self, context, parameters):
        try:
            return ActionResult(True, _service(context).run_project_tests(context, parameters))
        except subprocess.TimeoutExpired:
            return ActionResult(False, error="Test run timed out", error_code="TIMEOUT")
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="TEST_RUN_ERROR")


class ReadTestFailures(Action):
    name = "read_test_failures"
    description = "Read failure lines from a previously saved pytest report"
    category = ActionCategory.CODE
    parameters_schema = {"run_id": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        try:
            return ActionResult(True, _service(context).read_test_failures(context, parameters))
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="TEST_REPORT_ERROR")
