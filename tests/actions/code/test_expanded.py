import subprocess
from types import SimpleNamespace

from deskagent.actions.code.git_inspection import (
    CheckGitIgnored, GetGitAheadBehind, GetGitBlameLines, GetGitBranchInfo,
    GetGitCommitInfo, GetGitDiffSummary, GetGitFileHistory,
    GetGitRepositoryRoot, GetRecentGitCommits, ListGitBranches,
    ListGitConflictFiles, ListGitModifiedFiles, ListGitStagedFiles,
    ListGitTags, ListGitTrackedFiles, ListGitUntrackedFiles,
)
from deskagent.actions.code.source_inspection import (
    CheckPythonSyntax, FindDuplicateSourceFiles, FindLargeSourceFiles,
    FindPythonCalls, FindPythonSymbol, FindTodoComments,
    GetProjectLanguages, GetProjectManifests, GetProjectPythonImports,
    GetProjectSourceTree, GetPythonClassMembers, GetPythonFileOutline,
    GetPythonTestInventory, InspectSourceFile, ListProjectTestFiles,
    ListPythonImports, ReadProjectManifest, SearchProjectText,
)
from deskagent.actions.registry import create_action_registry
from deskagent.core.config import SecuritySettings, Settings


def context(tmp_path):
    return SimpleNamespace(settings=Settings(
        security=SecuritySettings(allowed_paths=[str(tmp_path)], blocked_paths=[])
    ))


def git(project, *args):
    return subprocess.run(["git", "-C", str(project), *args], capture_output=True,
                          text=True, check=True).stdout.strip()


def project(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "sample.py").write_text(
        "import os\n\nclass Widget:\n    def show(self):\n        return run_task()\n\ndef run_task():\n    return os.getcwd()  # TODO improve\n",
        encoding="utf-8",
    )
    (tmp_path / "copy.py").write_text((tmp_path / "sample.py").read_text(), encoding="utf-8")
    (tmp_path / "test_sample.py").write_text("def test_example():\n    assert True\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("pytest>=8\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("*.log\n", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "-c", "user.name=Test", "-c", "user.email=test@example.com",
        "commit", "-qm", "Initial project")
    commit = git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "sample.py").write_text(
        (tmp_path / "sample.py").read_text() + "\n# FIXME later\n", encoding="utf-8"
    )
    (tmp_path / "new.py").write_text("def new():\n    pass\n", encoding="utf-8")
    (tmp_path / "debug.log").write_text("ignored\n", encoding="utf-8")
    git(tmp_path, "add", "new.py")
    return commit


def test_structured_git_actions(tmp_path):
    commit = project(tmp_path)
    ctx = context(tmp_path)
    directory = str(tmp_path)
    base = {"directory": directory}
    assert GetGitRepositoryRoot().execute(ctx, base).data["root"] == directory
    assert GetGitBranchInfo().execute(ctx, base).data["head"] == commit
    assert ListGitBranches().execute(ctx, base).data["branches"]
    assert ListGitTags().execute(ctx, base).success
    assert GetRecentGitCommits().execute(ctx, base).data["commits"][0]["commit"] == commit
    info = GetGitCommitInfo().execute(ctx, {**base, "commit": commit})
    assert info.success, info.error
    assert "sample.py" in info.data["files"]
    assert ".env" not in info.data["files"]
    assert "sample.py" in ListGitTrackedFiles().execute(ctx, base).data["files"]
    assert ".env" not in ListGitTrackedFiles().execute(ctx, base).data["files"]
    assert ListGitUntrackedFiles().execute(ctx, base).data["files"] == []
    assert ListGitStagedFiles().execute(ctx, base).data["files"] == ["new.py"]
    assert ListGitModifiedFiles().execute(ctx, base).data["files"] == ["sample.py"]
    diff = GetGitDiffSummary().execute(ctx, base)
    assert diff.success and diff.data["files"][0]["path"] == "sample.py"
    assert ListGitConflictFiles().execute(ctx, base).data["total"] == 0
    history = GetGitFileHistory().execute(ctx, {**base, "path": "sample.py"})
    assert history.success and history.data["commits"][0]["commit"] == commit
    blame = GetGitBlameLines().execute(ctx, {
        **base, "path": "sample.py", "start_line": 1, "end_line": 2,
    })
    assert blame.success and "author Test" in blame.data["output"]
    assert CheckGitIgnored().execute(ctx, {**base, "path": "debug.log"}).data["ignored"]
    assert GetGitAheadBehind().execute(ctx, base).data["upstream"] is None


def test_source_tree_actions(tmp_path):
    project(tmp_path)
    ctx = context(tmp_path)
    base = {"directory": str(tmp_path)}
    tree = GetProjectSourceTree().execute(ctx, base)
    assert tree.success and "sample.py" in tree.data["files"]
    assert ".env" not in tree.data["files"]
    assert GetProjectLanguages().execute(ctx, base).data["extensions"][".py"]["files"] == 4
    assert InspectSourceFile().execute(ctx, {**base, "path": "sample.py"}).data["lines"] > 5
    assert SearchProjectText().execute(ctx, {**base, "query": "run_task"}).data["matches"]
    assert GetPythonFileOutline().execute(ctx, {**base, "path": "sample.py"}).data["symbols"][0]["name"] == "Widget"
    assert len(FindPythonSymbol().execute(ctx, {**base, "name": "run_task"}).data["matches"]) == 2
    assert ListPythonImports().execute(ctx, {**base, "path": "sample.py"}).data["imports"][0]["module"] == "os"
    assert FindTodoComments().execute(ctx, base).data["markers"]
    assert ListProjectTestFiles().execute(ctx, base).data["files"] == ["test_sample.py"]
    assert GetProjectManifests().execute(ctx, base).data["manifests"][0]["path"] == "requirements.txt"
    assert "pytest" in ReadProjectManifest().execute(ctx, {**base, "name": "requirements.txt"}).data["text"]
    assert FindDuplicateSourceFiles().execute(ctx, base).data["duplicates"] == []
    assert CheckPythonSyntax().execute(ctx, {**base, "path": "sample.py"}).data["valid"]
    assert GetPythonClassMembers().execute(ctx, {
        **base, "path": "sample.py", "class_name": "Widget",
    }).data["members"][0]["name"] == "show"
    assert len(FindPythonCalls().execute(ctx, {**base, "name": "run_task"}).data["calls"]) == 2
    assert GetProjectPythonImports().execute(ctx, base).data["packages"][0]["name"] == "os"
    assert FindLargeSourceFiles().execute(ctx, base).data["files"]
    assert GetPythonTestInventory().execute(ctx, base).data["tests"][0]["name"] == "test_example"


def test_project_path_and_secret_checks(tmp_path):
    project(tmp_path)
    ctx = context(tmp_path)
    base = {"directory": str(tmp_path)}
    assert not InspectSourceFile().execute(ctx, {**base, "path": "../outside.py"}).success
    assert not InspectSourceFile().execute(ctx, {**base, "path": ".env"}).success
    assert not GetGitFileHistory().execute(ctx, {**base, "path": ".env"}).success
    assert not GetGitCommitInfo().execute(ctx, {**base, "commit": "HEAD"}).success


def test_code_actions_are_registered():
    names = create_action_registry(include_plugins=False).names()
    for name in ("get_git_branch_info", "get_git_diff_summary", "get_project_source_tree",
                 "find_python_symbol", "search_project_text"):
        assert name in names
