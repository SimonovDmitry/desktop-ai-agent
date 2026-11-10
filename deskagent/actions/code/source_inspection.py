"""Bounded source-tree inspection without executing project code."""
from __future__ import annotations

import ast
import collections
import hashlib
import re

from deskagent.actions.code._common import (
    CodeAction, project_dir, read_source, safe_file, walk_sources,
)

DIR = {"directory": {"type": "string", "required": True}}
PATH = {**DIR, "path": {"type": "string", "required": True}}
MANIFESTS = {"pyproject.toml", "requirements.txt", "setup.cfg", "package.json",
             "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "Makefile",
             "pytest.ini", "tox.ini", ".pre-commit-config.yaml"}


def _project(context, parameters):
    return project_dir(context, parameters["directory"])


class GetProjectSourceTree(CodeAction):
    name = "get_project_source_tree"
    description = "List bounded source paths while skipping dependency and secret directories"
    parameters_schema = {**DIR, "limit": {"type": "integer", "required": False,
                                          "default": 300, "minimum": 1, "maximum": 1000}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            limit = parameters.get("limit", 300)
            if not 1 <= limit <= 1000:
                raise ValueError("Tree limit must be 1-1000")
            files = [str(path.relative_to(project)) for path in walk_sources(context, project)]
            return {"directory": str(project), "files": files[:limit],
                    "total": len(files), "truncated": len(files) > limit}
        return self.run(operation)


class GetProjectLanguages(CodeAction):
    name = "get_project_languages"
    description = "Count source files and bytes by file extension"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            counts = collections.defaultdict(lambda: {"files": 0, "bytes": 0})
            for path in walk_sources(context, project):
                item = counts[path.suffix.lower() or "(none)"]
                item["files"] += 1
                item["bytes"] += path.stat().st_size
            return {"directory": str(project), "extensions": dict(sorted(counts.items()))}
        return self.run(operation)


class InspectSourceFile(CodeAction):
    name = "inspect_source_file"
    description = "Read bounded line, byte, and blank-line counts for one source file"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            path, text = read_source(context, project, parameters["path"])
            lines = text.splitlines()
            return {"directory": str(project), "path": str(path.relative_to(project)),
                    "bytes": path.stat().st_size, "lines": len(lines),
                    "blank_lines": sum(not line.strip() for line in lines),
                    "longest_line": max((len(line) for line in lines), default=0)}
        return self.run(operation)


class SearchProjectText(CodeAction):
    name = "search_project_text"
    description = "Search a literal phrase in bounded source files with line excerpts"
    parameters_schema = {**DIR, "query": {"type": "string", "required": True},
                         "max_results": {"type": "integer", "required": False,
                                         "default": 100, "minimum": 1, "maximum": 500}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            query = parameters["query"].strip()
            limit = parameters.get("max_results", 100)
            if not query or len(query) > 200 or not 1 <= limit <= 500:
                raise ValueError("Query must contain 1-200 characters and result limit 1-500")
            matches, scanned = [], 0
            for path in walk_sources(context, project):
                scanned += 1
                try:
                    text = path.read_text(encoding="utf-8-sig")
                except UnicodeError:
                    continue
                for number, line in enumerate(text.splitlines(), 1):
                    if query.casefold() in line.casefold():
                        matches.append({"path": str(path.relative_to(project)), "line": number,
                                        "excerpt": line[:500]})
                        if len(matches) >= limit:
                            return {"directory": str(project), "matches": matches,
                                    "scanned_files": scanned, "truncated": True}
            return {"directory": str(project), "matches": matches,
                    "scanned_files": scanned, "truncated": False}
        return self.run(operation)


class GetPythonFileOutline(CodeAction):
    name = "get_python_file_outline"
    description = "List top-level Python classes and functions with line numbers"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            path, text = read_source(context, project, parameters["path"])
            if path.suffix.lower() not in {".py", ".pyi"}:
                raise ValueError("Python source file is required")
            tree = ast.parse(text)
            symbols = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    symbols.append({"name": node.name, "line": node.lineno,
                                    "end_line": node.end_lineno,
                                    "kind": "class" if isinstance(node, ast.ClassDef)
                                    else "async_function" if isinstance(node, ast.AsyncFunctionDef)
                                    else "function"})
            return {"directory": str(project), "path": str(path.relative_to(project)),
                    "symbols": symbols[:500], "total": len(symbols),
                    "truncated": len(symbols) > 500}
        return self.run(operation)


class FindPythonSymbol(CodeAction):
    name = "find_python_symbol"
    description = "Find exact Python class and function definitions across a project"
    parameters_schema = {**DIR, "name": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            name = parameters["name"]
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,100}", name):
                raise ValueError("Symbol name must be a Python identifier")
            matches, scanned = [], 0
            for path in walk_sources(context, project):
                if path.suffix.lower() not in {".py", ".pyi"}:
                    continue
                scanned += 1
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
                except (SyntaxError, UnicodeError):
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                        matches.append({"path": str(path.relative_to(project)),
                                        "line": node.lineno, "kind": type(node).__name__})
                        if len(matches) >= 500:
                            return {"directory": str(project), "matches": matches,
                                    "scanned_files": scanned, "truncated": True}
            return {"directory": str(project), "matches": matches,
                    "scanned_files": scanned, "truncated": False}
        return self.run(operation)


class ListPythonImports(CodeAction):
    name = "list_python_imports"
    description = "List imported Python modules in one source file"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            path, text = read_source(context, project, parameters["path"])
            if path.suffix.lower() not in {".py", ".pyi"}:
                raise ValueError("Python source file is required")
            imports = []
            for node in ast.walk(ast.parse(text)):
                if isinstance(node, ast.Import):
                    imports.extend({"module": alias.name, "line": node.lineno} for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append({"module": "." * node.level + (node.module or ""),
                                    "line": node.lineno})
            return {"directory": str(project), "path": str(path.relative_to(project)),
                    "imports": imports[:500], "total": len(imports),
                    "truncated": len(imports) > 500}
        return self.run(operation)


class FindTodoComments(CodeAction):
    name = "find_todo_comments"
    description = "Locate TODO, FIXME and XXX markers in source lines"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            found = []
            pattern = re.compile(r"\b(TODO|FIXME|XXX)\b", re.IGNORECASE)
            for path in walk_sources(context, project):
                try:
                    text = path.read_text(encoding="utf-8-sig")
                except UnicodeError:
                    continue
                for number, line in enumerate(text.splitlines(), 1):
                    if match := pattern.search(line):
                        found.append({"path": str(path.relative_to(project)),
                                      "line": number, "marker": match.group(1).upper(),
                                      "excerpt": line[:300]})
                        if len(found) >= 500:
                            return {"directory": str(project), "markers": found, "truncated": True}
            return {"directory": str(project), "markers": found, "truncated": False}
        return self.run(operation)


class ListProjectTestFiles(CodeAction):
    name = "list_project_test_files"
    description = "List files likely to contain project tests"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            files = [str(path.relative_to(project)) for path in walk_sources(context, project)
                     if path.name.startswith("test_") or path.name.endswith(("_test.py", ".test.js", ".test.ts"))]
            return {"directory": str(project), "files": files[:500],
                    "total": len(files), "truncated": len(files) > 500}
        return self.run(operation)


class GetProjectManifests(CodeAction):
    name = "get_project_manifests"
    description = "Locate common dependency, build and test configuration files"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            found = []
            for name in sorted(MANIFESTS):
                try:
                    path = safe_file(context, project, name)
                except (FileNotFoundError, PermissionError):
                    continue
                found.append({"path": name, "bytes": path.stat().st_size})
            return {"directory": str(project), "manifests": found}
        return self.run(operation)


class ReadProjectManifest(CodeAction):
    name = "read_project_manifest"
    description = "Read a bounded common project manifest by exact file name"
    parameters_schema = {**DIR, "name": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            name = parameters["name"]
            if name not in MANIFESTS:
                raise ValueError("Unsupported manifest name")
            path = safe_file(context, project, name)
            if path.stat().st_size > 100_000:
                raise ValueError("Manifest exceeds 100 KB")
            text = path.read_text(encoding="utf-8-sig")
            return {"directory": str(project), "name": name, "text": text}
        return self.run(operation)


class FindDuplicateSourceFiles(CodeAction):
    name = "find_duplicate_source_files"
    description = "Find identical source files by SHA-256 without returning their content"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            groups = collections.defaultdict(list)
            for path in walk_sources(context, project):
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                groups[digest].append(str(path.relative_to(project)))
            duplicates = [{"sha256": digest, "paths": paths}
                          for digest, paths in groups.items() if len(paths) > 1]
            return {"directory": str(project), "duplicates": duplicates[:100],
                    "total": len(duplicates), "truncated": len(duplicates) > 100}
        return self.run(operation)


class CheckPythonSyntax(CodeAction):
    name = "check_python_syntax"
    description = "Parse one Python file and report syntax errors without executing code"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            path, text = read_source(context, project, parameters["path"])
            if path.suffix.lower() not in {".py", ".pyi"}:
                raise ValueError("Python source file is required")
            try:
                ast.parse(text)
                error = None
            except SyntaxError as exc:
                error = {"line": exc.lineno, "column": exc.offset, "message": exc.msg}
            return {"directory": str(project), "path": str(path.relative_to(project)),
                    "valid": error is None, "error": error}
        return self.run(operation)


class GetPythonClassMembers(CodeAction):
    name = "get_python_class_members"
    description = "List methods and nested classes of one named Python class"
    parameters_schema = {**PATH, "class_name": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            path, text = read_source(context, project, parameters["path"])
            if path.suffix.lower() not in {".py", ".pyi"}:
                raise ValueError("Python source file is required")
            classes = [node for node in ast.walk(ast.parse(text))
                       if isinstance(node, ast.ClassDef) and node.name == parameters["class_name"]]
            if len(classes) != 1:
                raise ValueError("Class name must identify exactly one class in the file")
            members = [{"name": node.name, "line": node.lineno,
                        "kind": "class" if isinstance(node, ast.ClassDef)
                        else "async_method" if isinstance(node, ast.AsyncFunctionDef)
                        else "method"}
                       for node in classes[0].body
                       if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
            return {"directory": str(project), "path": str(path.relative_to(project)),
                    "class_name": parameters["class_name"], "members": members[:500],
                    "total": len(members), "truncated": len(members) > 500}
        return self.run(operation)


class FindPythonCalls(CodeAction):
    name = "find_python_calls"
    description = "Find syntactic calls to an exact Python function or method name"
    parameters_schema = {**DIR, "name": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            name = parameters["name"]
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,100}", name):
                raise ValueError("Call name must be a Python identifier")
            matches = []
            for path in walk_sources(context, project):
                if path.suffix.lower() not in {".py", ".pyi"}:
                    continue
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
                except (SyntaxError, UnicodeError):
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        function = node.func
                        called = function.id if isinstance(function, ast.Name) else (
                            function.attr if isinstance(function, ast.Attribute) else None
                        )
                        if called == name:
                            matches.append({"path": str(path.relative_to(project)), "line": node.lineno})
                            if len(matches) >= 500:
                                return {"directory": str(project), "calls": matches, "truncated": True}
            return {"directory": str(project), "calls": matches, "truncated": False}
        return self.run(operation)


class GetProjectPythonImports(CodeAction):
    name = "get_project_python_imports"
    description = "Count top-level imported Python packages across source files"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            counts = collections.Counter()
            parsed = 0
            for path in walk_sources(context, project):
                if path.suffix.lower() not in {".py", ".pyi"}:
                    continue
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
                except (SyntaxError, UnicodeError):
                    continue
                parsed += 1
                packages = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        packages.update(alias.name.split(".")[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                        packages.add(node.module.split(".")[0])
                counts.update(packages)
            return {"directory": str(project), "parsed_files": parsed,
                    "packages": [{"name": name, "files": count}
                                 for name, count in counts.most_common(200)],
                    "truncated": len(counts) > 200}
        return self.run(operation)


class FindLargeSourceFiles(CodeAction):
    name = "find_large_source_files"
    description = "List the largest bounded source files in a project"
    parameters_schema = {**DIR, "limit": {"type": "integer", "required": False,
                                          "default": 20, "minimum": 1, "maximum": 100}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            limit = parameters.get("limit", 20)
            if not 1 <= limit <= 100:
                raise ValueError("Limit must be 1-100")
            files = sorted(({"path": str(path.relative_to(project)), "bytes": path.stat().st_size}
                            for path in walk_sources(context, project)),
                           key=lambda item: item["bytes"], reverse=True)
            return {"directory": str(project), "files": files[:limit],
                    "total": len(files), "truncated": len(files) > limit}
        return self.run(operation)


class GetPythonTestInventory(CodeAction):
    name = "get_python_test_inventory"
    description = "List pytest-style test functions and class methods without importing tests"
    parameters_schema = DIR
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            project = _project(context, parameters)
            tests = []
            for path in walk_sources(context, project):
                if path.suffix.lower() != ".py" or not (
                    path.name.startswith("test_") or path.name.endswith("_test.py")
                ):
                    continue
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
                except (SyntaxError, UnicodeError):
                    continue
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                        tests.append({"path": str(path.relative_to(project)), "line": node.lineno,
                                      "name": node.name})
                    elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                        for child in node.body:
                            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                                tests.append({"path": str(path.relative_to(project)), "line": child.lineno,
                                              "name": f"{node.name}.{child.name}"})
                    if len(tests) >= 1000:
                        return {"directory": str(project), "tests": tests[:1000], "truncated": True}
            return {"directory": str(project), "tests": tests, "truncated": False}
        return self.run(operation)
