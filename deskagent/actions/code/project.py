from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.privacy.guards import FilesystemGuard


DIRECTORY = {"directory": {"type": "string", "required": True}}


def _project(parameters):
    project = Path(parameters["directory"]).expanduser().resolve()
    if not project.is_dir():
        raise NotADirectoryError(project)
    return project


def _git(project, *args):
    result = subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[:1000] or "Git command failed")
    output = result.stdout
    return {"output": output[:100000], "truncated": len(output) > 100000}


class GetGitStatus(Action):
    name = "get_git_status"
    description = "Read the branch and changed files in a local Git worktree"
    category = ActionCategory.CODE
    parameters_schema = DIRECTORY

    def execute(self, context, parameters):
        try:
            project = _project(parameters)
            return ActionResult(True, {"directory": str(project), **_git(project, "status", "--short", "--branch")})
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
                names = _git(project, *args, "--name-only", "-z")["output"]
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
                "directory": str(project), **_git(project, *args), "excluded_sensitive_files": excluded,
            })
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="GIT_ERROR")


def _run_path(context, create=True):
    root = Path(context.settings.storage.autopilot).expanduser().parent / "test-runs"
    if create:
        root.mkdir(parents=True, exist_ok=True)
        root.chmod(0o700)
    return root


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
            project = _project(parameters)
            security = context.settings.security
            guard = FilesystemGuard(security.allowed_paths, security.blocked_paths)
            decision = guard.check("write_project_test_output", {"directory": str(project)})
            if not decision.allowed:
                raise PermissionError(decision.reason)
            target = parameters.get("target")
            command = [sys.executable, "-m", "pytest", "-q"]
            if target:
                selected = (project / target).resolve()
                if not selected.is_relative_to(project):
                    raise ValueError("Test target is outside the project")
                command.append(str(selected.relative_to(project)))
            result = subprocess.run(command, cwd=project, capture_output=True, text=True,
                                    timeout=parameters.get("timeout", 120))
            run_id = uuid.uuid4().hex
            output = (result.stdout + "\n" + result.stderr)[:200000]
            report = {"run_id": run_id, "directory": str(project), "target": target,
                      "exit_code": result.returncode, "output": output,
                      "created_at": datetime.now(UTC).isoformat()}
            destination = _run_path(context) / f"{run_id}.json"
            destination.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            destination.chmod(0o600)
            return ActionResult(True, {"run_id": run_id, "exit_code": result.returncode,
                                       "passed": result.returncode == 0, "output_tail": output[-4000:]})
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
            run_id = parameters["run_id"]
            if len(run_id) != 32 or any(char not in "0123456789abcdef" for char in run_id):
                raise ValueError("Invalid test run id")
            path = _run_path(context, create=False) / f"{run_id}.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            lines = report["output"].splitlines()
            failures = [line for line in lines if line.startswith(("FAILED ", "ERROR ", "E   "))]
            return ActionResult(True, {"run_id": run_id, "exit_code": report["exit_code"],
                                       "failures": failures[:100], "output_tail": report["output"][-4000:]})
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="TEST_REPORT_ERROR")
