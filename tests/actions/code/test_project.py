import subprocess
from types import SimpleNamespace

from deskagent.actions.code.project import ReadTestFailures, RunProjectTests, ShowGitDiff
from deskagent.core.config import SecuritySettings, Settings, StorageSettings


def _context(tmp_path):
    settings = Settings(
        security=SecuritySettings(allowed_paths=[str(tmp_path)], blocked_paths=[]),
        storage=StorageSettings(autopilot=str(tmp_path / "state" / "autopilot.sqlite")),
    )
    return SimpleNamespace(settings=settings)


def test_show_git_diff_excludes_sensitive_files(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "notes.txt").write_text("safe text\n", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "notes.txt", ".env"], check=True)
    result = ShowGitDiff().execute(_context(tmp_path), {"directory": str(tmp_path), "staged": True})
    assert result.success
    assert "safe text" in result.data["output"]
    assert "TOKEN=secret" not in result.data["output"]


def test_run_tests_saves_report_and_reads_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "deskagent.actions.code.project.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="FAILED tests/test_x.py::test_x\n", stderr=""),
    )
    context = _context(tmp_path)
    run = RunProjectTests().execute(context, {"directory": str(tmp_path)})
    assert run.success and not run.data["passed"]
    report = ReadTestFailures().execute(context, {"run_id": run.data["run_id"]})
    assert report.success
    assert report.data["failures"] == ["FAILED tests/test_x.py::test_x"]
