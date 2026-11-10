"""Structured read-only Git actions."""
from __future__ import annotations

from deskagent.actions.code._common import (
    CodeAction, commit_id, git, git_names, project_dir, safe_file,
)

DIR = {"directory": {"type": "string", "required": True}}
PATH = {**DIR, "path": {"type": "string", "required": True}}


def _project(context, parameters):
    return project_dir(context, parameters["directory"])


class GetGitRepositoryRoot(CodeAction):
    name = "get_git_repository_root"
    description = "Identify the Git repository root and current branch"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            root, _ = git(project, "rev-parse", "--show-toplevel")
            branch, _ = git(project, "branch", "--show-current")
            return {"directory": str(project), "root": root.strip(), "branch": branch.strip() or None}
        return self.run(operation)


class GetGitBranchInfo(CodeAction):
    name = "get_git_branch_info"
    description = "Read branch, HEAD commit and upstream relationship"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            head, _ = git(project, "rev-parse", "HEAD")
            branch, _ = git(project, "branch", "--show-current")
            upstream = None
            try:
                upstream, _ = git(project, "rev-parse", "--abbrev-ref", "@{upstream}")
                upstream = upstream.strip()
            except RuntimeError:
                pass
            return {"directory": str(project), "head": head.strip(),
                    "branch": branch.strip() or None, "upstream": upstream}
        return self.run(operation)


class ListGitBranches(CodeAction):
    name = "list_git_branches"
    description = "List bounded local Git branches with commit ids"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            output, truncated = git(project, "for-each-ref", "--format=%(refname:short)%09%(objectname)",
                                    "refs/heads", max_output=100_000)
            branches = []
            for line in output.splitlines()[:200]:
                if "\t" in line:
                    name, commit = line.split("\t", 1)
                    branches.append({"name": name, "commit": commit})
            return {"directory": str(project), "branches": branches,
                    "truncated": truncated or len(output.splitlines()) > 200}
        return self.run(operation)


class ListGitTags(CodeAction):
    name = "list_git_tags"
    description = "List bounded Git tags without resolving tag contents"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            output, truncated = git(project, "tag", "--list", max_output=100_000)
            tags = output.splitlines()
            return {"directory": str(project), "tags": tags[:200],
                    "truncated": truncated or len(tags) > 200}
        return self.run(operation)


class GetRecentGitCommits(CodeAction):
    name = "get_recent_git_commits"
    description = "Read recent commit ids, dates, authors and subjects"
    parameters_schema = {**DIR, "limit": {"type": "integer", "required": False,
                                          "default": 20, "minimum": 1, "maximum": 100}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            limit = parameters.get("limit", 20)
            if not 1 <= limit <= 100:
                raise ValueError("Commit limit must be 1-100")
            output, truncated = git(project, "log", f"-{limit}",
                                    "--format=%H%x09%aI%x09%an%x09%s", max_output=100_000)
            commits = []
            for line in output.splitlines():
                pieces = line.split("\t", 3)
                if len(pieces) == 4:
                    commits.append(dict(zip(("commit", "date", "author", "subject"), pieces)))
            return {"directory": str(project), "commits": commits, "truncated": truncated}
        return self.run(operation)


class GetGitCommitInfo(CodeAction):
    name = "get_git_commit_info"
    description = "Read a commit's metadata and changed file names"
    parameters_schema = {**DIR, "commit": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            commit = commit_id(parameters["commit"])
            output, _ = git(project, "show", "--no-patch",
                            "--format=%H%x09%aI%x09%an%x09%s", commit, max_output=5000)
            pieces = output.strip().split("\t", 3)
            names, excluded = git_names(context, project, "diff-tree", "--root", "--no-commit-id",
                                        "--name-only", "-r", commit)
            return {"directory": str(project), "commit": pieces[0], "date": pieces[1],
                    "author": pieces[2], "subject": pieces[3], "files": names[:500],
                    "excluded_sensitive_files": excluded, "truncated": len(names) > 500}
        return self.run(operation)


class ListGitTrackedFiles(CodeAction):
    name = "list_git_tracked_files"
    description = "List tracked project files excluding sensitive paths"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            names, excluded = git_names(context, project, "ls-files", "--cached")
            return {"directory": str(project), "files": names[:500], "total": len(names),
                    "truncated": len(names) > 500, "excluded_sensitive_files": excluded}
        return self.run(operation)


class ListGitUntrackedFiles(CodeAction):
    name = "list_git_untracked_files"
    description = "List untracked non-ignored files excluding sensitive paths"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            names, excluded = git_names(context, project, "ls-files", "--others", "--exclude-standard")
            return {"directory": str(project), "files": names[:500], "total": len(names),
                    "truncated": len(names) > 500, "excluded_sensitive_files": excluded}
        return self.run(operation)


class ListGitStagedFiles(CodeAction):
    name = "list_git_staged_files"
    description = "List staged file changes excluding sensitive paths"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            names, excluded = git_names(context, project, "diff", "--cached", "--name-only",
                                        "--no-ext-diff", "--no-textconv")
            return {"directory": str(project), "files": names[:500], "total": len(names),
                    "truncated": len(names) > 500, "excluded_sensitive_files": excluded}
        return self.run(operation)


class ListGitModifiedFiles(CodeAction):
    name = "list_git_modified_files"
    description = "List unstaged modified files excluding sensitive paths"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            names, excluded = git_names(context, project, "diff", "--name-only",
                                        "--no-ext-diff", "--no-textconv")
            return {"directory": str(project), "files": names[:500], "total": len(names),
                    "truncated": len(names) > 500, "excluded_sensitive_files": excluded}
        return self.run(operation)


class GetGitDiffSummary(CodeAction):
    name = "get_git_diff_summary"
    description = "Read bounded insertion and deletion counts by changed file"
    parameters_schema = {**DIR, "staged": {"type": "boolean", "required": False, "default": False}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            args = ["diff", "--name-only", "--no-ext-diff", "--no-textconv"]
            if parameters.get("staged"):
                args.append("--cached")
            names, excluded = git_names(context, project, *args)
            if not names:
                return {"directory": str(project), "files": [], "excluded_sensitive_files": excluded}
            args = ["diff", "--numstat", "-z", "--no-ext-diff", "--no-textconv"]
            if parameters.get("staged"):
                args.append("--cached")
            output, truncated = git(project, *args, "--", *names)
            entries = []
            records = [record for record in output.split("\0") if record]
            for line in records[:500]:
                pieces = line.split("\t", 2)
                if len(pieces) == 3:
                    entries.append({"added": None if pieces[0] == "-" else int(pieces[0]),
                                    "removed": None if pieces[1] == "-" else int(pieces[1]),
                                    "path": pieces[2]})
            return {"directory": str(project), "files": entries,
                    "excluded_sensitive_files": excluded,
                    "truncated": truncated or len(records) > 500}
        return self.run(operation)


class ListGitConflictFiles(CodeAction):
    name = "list_git_conflict_files"
    description = "List unresolved merge-conflict paths"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            names, excluded = git_names(context, project, "diff", "--name-only", "--diff-filter=U")
            return {"directory": str(project), "files": names[:500], "total": len(names),
                    "truncated": len(names) > 500, "excluded_sensitive_files": excluded}
        return self.run(operation)


class GetGitFileHistory(CodeAction):
    name = "get_git_file_history"
    description = "Read recent commit history for one allowed project file"
    parameters_schema = {**PATH, "limit": {"type": "integer", "required": False,
                                           "default": 20, "minimum": 1, "maximum": 100}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            path = safe_file(context, project, parameters["path"], required=False)
            limit = parameters.get("limit", 20)
            if not 1 <= limit <= 100:
                raise ValueError("History limit must be 1-100")
            output, truncated = git(project, "log", "--follow", f"-{limit}",
                                    "--format=%H%x09%aI%x09%s", "--",
                                    str(path.relative_to(project)), max_output=100_000)
            commits = []
            for line in output.splitlines():
                pieces = line.split("\t", 2)
                if len(pieces) == 3:
                    commits.append({"commit": pieces[0], "date": pieces[1], "subject": pieces[2]})
            return {"directory": str(project), "path": str(path.relative_to(project)),
                    "commits": commits, "truncated": truncated}
        return self.run(operation)


class GetGitBlameLines(CodeAction):
    name = "get_git_blame_lines"
    description = "Read commit attribution for a bounded line range of one file"
    parameters_schema = {**PATH, "start_line": {"type": "integer", "required": True,
                                                "minimum": 1},
                         "end_line": {"type": "integer", "required": True, "minimum": 1}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            path = safe_file(context, project, parameters["path"])
            start, end = parameters["start_line"], parameters["end_line"]
            if start < 1 or end < start or end - start >= 200:
                raise ValueError("Blame range must contain 1-200 lines")
            output, truncated = git(project, "blame", "--line-porcelain",
                                    "-L", f"{start},{end}", "--",
                                    str(path.relative_to(project)), max_output=100_000)
            return {"directory": str(project), "path": str(path.relative_to(project)),
                    "output": output, "truncated": truncated}
        return self.run(operation)


class CheckGitIgnored(CodeAction):
    name = "check_git_ignored"
    description = "Check whether a project path is excluded by Git ignore rules"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            path = safe_file(context, project, parameters["path"], required=False)
            # check-ignore uses exit status 1 for a non-ignored path.
            import subprocess
            process = subprocess.run(["git", "-C", str(project), "check-ignore", "-q", "--",
                                      str(path.relative_to(project))], capture_output=True, timeout=20)
            if process.returncode not in {0, 1}:
                raise RuntimeError(process.stderr.decode(errors="replace")[:1000])
            return {"directory": str(project), "path": str(path.relative_to(project)),
                    "ignored": process.returncode == 0}
        return self.run(operation)


class GetGitAheadBehind(CodeAction):
    name = "get_git_ahead_behind"
    description = "Count local commits ahead of and behind the configured upstream"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            try:
                upstream, _ = git(project, "rev-parse", "--abbrev-ref", "@{upstream}")
            except RuntimeError:
                return {"directory": str(project), "upstream": None, "ahead": None, "behind": None}
            output, _ = git(project, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
            ahead, behind = map(int, output.split())
            return {"directory": str(project), "upstream": upstream.strip(),
                    "ahead": ahead, "behind": behind}
        return self.run(operation)
