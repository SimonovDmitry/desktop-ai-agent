from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class CreateArchive(Action):
    name = "create_archive"
    description = "Compress multiple files or directories into a single archive"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "files": {"type": "list", "required": True, "description": "List of paths to include"},
        "destination": {"type": "string", "required": True, "description": "Path to the resulting archive"},
        "format": {"type": "string", "required": False, "default": "zip", "enum": ["zip", "tar", "gztar", "bztar", "xztar"]}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            result = context.services.file.archive.create(p['files'], p['destination'], p.get('format', 'zip'))
            return ActionResult(success=True, data={
                "created": True,
                "path": p['destination'],
                "files_count": len(p['files']),
                "size": result.get('size')
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ExtractArchive(Action):
    name = "extract_archive"
    description = "Decompress an archive to a specified directory"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "archive": {"type": "string", "required": True},
        "destination": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        archive, dest = parameters.get('archive'), parameters.get('destination')
        try:
            context.services.file.archive.extract(archive, dest)
            return ActionResult(success=True, data={"extracted": True, "destination": dest})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ListArchiveContents(Action):
    name = "list_archive_contents"
    description = "List all files and folders inside an archive without extracting it"
    category = ActionCategory.FILE
    parameters_schema = {"archive": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        archive = parameters.get('archive')
        try:
            contents = context.services.file.archive.list_contents(archive)
            return ActionResult(success=True, data={"entries": contents, "count": len(contents)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class AddToArchive(Action):
    name = "add_to_archive"
    description = "Add new files to an existing archive"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "archive": {"type": "string", "required": True},
        "files": {"type": "list", "required": True}
    }

    def execute(self, context, parameters):
        archive, files = parameters.get('archive'), parameters.get('files')
        try:
            context.services.file.archive.add_files(archive, files)
            return ActionResult(success=True, data={"added": True, "count": len(files)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RemoveFromArchive(Action):
    name = "remove_from_archive"
    description = "Remove specific files from inside an archive"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "archive": {"type": "string", "required": True},
        "file_names": {"type": "list", "required": True, "description": "Internal paths inside the archive"}
    }

    def execute(self, context, parameters):
        archive, names = parameters.get('archive'), parameters.get('file_names')
        try:
            context.services.file.archive.remove_files(archive, names)
            return ActionResult(success=True, data={"removed": True, "count": len(names)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class TestArchive(Action):
    name = "test_archive"
    description = "Check the integrity of an archive file"
    category = ActionCategory.FILE
    parameters_schema = {"archive": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        archive = parameters.get('archive')
        try:
            is_valid = context.services.file.archive.test(archive)
            return ActionResult(success=True, data={"valid": is_valid})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetArchiveInfo(Action):
    name = "get_archive_info"
    description = "Get detailed information about the archive format, size, and compression"
    category = ActionCategory.FILE
    parameters_schema = {"archive": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        archive = parameters.get('archive')
        try:
            info = context.services.file.archive.get_info(archive)
            return ActionResult(success=True, data=info)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))