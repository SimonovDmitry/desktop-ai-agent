from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class CompareFiles(Action):
    name = "compare_files"
    description = "Perform a basic comparison of two files (size, hash, metadata)"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "file1": {"type": "string", "required": True},
        "file2": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        f1, f2 = parameters.get('file1'), parameters.get('file2')
        try:
            result = context.services.file.comparison.compare_files(f1, f2)
            return ActionResult(success=True, data=result)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CompareFileContents(Action):
    name = "compare_file_contents"
    description = "Compare the content of two text files and return if they are identical"
    category = ActionCategory.FILE
    parameters_schema = {
        "file1": {"type": "string", "required": True},
        "file2": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        f1, f2 = parameters.get('file1'), parameters.get('file2')
        try:
            comparison = context.services.file.comparison.compare_contents(f1, f2)
            return ActionResult(success=True, data=comparison)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileHash(Action):
    name = "get_file_hash"
    description = "Calculate the cryptographic hash of a file"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "algorithm": {"type": "string", "required": False, "default": "sha256", "enum": ["md5", "sha1", "sha256"]}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        alg = parameters.get('algorithm', 'sha256')
        try:
            file_hash = context.services.file.comparison.get_hash(path, alg)
            return ActionResult(success=True, data={"algorithm": alg, "hash": file_hash})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class VerifyFileHash(Action):
    name = "verify_file_hash"
    description = "Verify that a file matches an expected hash value"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "expected_hash": {"type": "string", "required": True},
        "algorithm": {"type": "string", "required": False, "default": "sha256"}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        expected = parameters.get('expected_hash')
        alg = parameters.get('algorithm', 'sha256')
        try:
            is_valid = context.services.file.comparison.verify_hash(path, expected, alg)
            return ActionResult(success=True, data={"valid": is_valid, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindDifferences(Action):
    name = "find_differences"
    description = "Find specific line-by-line differences between two text files"
    category = ActionCategory.FILE
    parameters_schema = {
        "file1": {"type": "string", "required": True},
        "file2": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        f1, f2 = parameters.get('file1'), parameters.get('file2')
        try:
            diffs = context.services.file.comparison.get_diff(f1, f2)
            return ActionResult(success=True, data={"differences": diffs, "identical": len(diffs) == 0})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class AreFilesIdentical(Action):
    name = "are_files_identical"
    description = "Quick check to see if two files are exactly the same"
    category = ActionCategory.FILE
    parameters_schema = {
        "file1": {"type": "string", "required": True},
        "file2": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        f1, f2 = parameters.get('file1'), parameters.get('file2')
        try:
            identical = context.services.file.comparison.is_identical(f1, f2)
            return ActionResult(success=True, data={"identical": identical})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))