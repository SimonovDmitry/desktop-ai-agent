"""Project command execution and private pytest reports."""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from deskagent.privacy.guards import FilesystemGuard


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


def _run_path(context, create=True):
    root = Path(context.settings.storage.autopilot).expanduser().parent / "test-runs"
    if create:
        root.mkdir(parents=True, exist_ok=True)
        root.chmod(0o700)
    return root


def run_project_tests(context, parameters):
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
    return {"run_id": run_id, "exit_code": result.returncode,
            "passed": result.returncode == 0, "output_tail": output[-4000:]}


def read_test_failures(context, parameters):
    run_id = parameters["run_id"]
    if len(run_id) != 32 or any(char not in "0123456789abcdef" for char in run_id):
        raise ValueError("Invalid test run id")
    path = _run_path(context, create=False) / f"{run_id}.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    lines = report["output"].splitlines()
    failures = [line for line in lines if line.startswith(("FAILED ", "ERROR ", "E   "))]
    return {"run_id": run_id, "exit_code": report["exit_code"],
            "failures": failures[:100], "output_tail": report["output"][-4000:]}
