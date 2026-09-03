from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetFileInfo(Action):
    name = "get_file_info"
    description = "Get comprehensive information about a file or directory"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "path": {"type": "string", "required": True, "description": "Path to the file or directory"}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            info = context.services.file.information.get_info(path)
            return ActionResult(success=True, data=info)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="FILE_NOT_FOUND")


class GetFileMetadata(Action):
    name = "get_file_metadata"
    description = "Get extended metadata (permissions, owner, group, flags)"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "path": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            meta = context.services.file.information.get_metadata(path)
            return ActionResult(success=True, data=meta)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileSize(Action):
    name = "get_file_size"
    description = "Get the size of a file in bytes"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            size = context.services.file.information.get_size(path)
            return ActionResult(success=True, data={"size": size, "unit": "bytes"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileType(Action):
    name = "get_file_type"
    description = "Determine if the path is a file, directory, symlink, etc."
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            f_type = context.services.file.information.get_type(path)
            return ActionResult(success=True, data={"type": f_type})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileExtension(Action):
    name = "get_file_extension"
    description = "Get the file extension (e.g., .pdf, .txt)"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            ext = context.services.file.information.get_extension(path)
            return ActionResult(success=True, data={"extension": ext})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileMimeType(Action):
    name = "get_file_mime_type"
    description = "Get the MIME type of a file (e.g., application/pdf)"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            mime = context.services.file.information.get_mime_type(path)
            return ActionResult(success=True, data={"mime_type": mime})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFilePath(Action):
    name = "get_file_path"
    description = "Get the absolute normalized path"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            abs_path = context.services.file.information.get_absolute_path(path)
            return ActionResult(success=True, data={"path": abs_path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileName(Action):
    name = "get_file_name"
    description = "Get only the filename from a path"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            name = context.services.file.information.get_name(path)
            return ActionResult(success=True, data={"name": name})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileDirectory(Action):
    name = "get_file_directory"
    description = "Get the parent directory path"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            directory = context.services.file.information.get_directory(path)
            return ActionResult(success=True, data={"directory": directory})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileCreatedTime(Action):
    name = "get_file_created_time"
    description = "Get the creation timestamp"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            ts = context.services.file.information.get_created_at(path)
            return ActionResult(success=True, data={"created_at": ts})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileModifiedTime(Action):
    name = "get_file_modified_time"
    description = "Get the last modification timestamp"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            ts = context.services.file.information.get_modified_at(path)
            return ActionResult(success=True, data={"modified_at": ts})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileAccessedTime(Action):
    name = "get_file_accessed_time"
    description = "Get the last access timestamp"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            ts = context.services.file.information.get_accessed_at(path)
            return ActionResult(success=True, data={"accessed_at": ts})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsFile(Action):
    name = "is_file"
    description = "Check if the path points to a regular file"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            result = context.services.file.information.is_file(path)
            return ActionResult(success=True, data={"is_file": result})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsDirectory(Action):
    name = "is_directory"
    description = "Check if the path is a directory"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            result = context.services.file.information.is_directory(path)
            return ActionResult(success=True, data={"is_directory": result})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsSymlink(Action):
    name = "is_symlink"
    description = "Check if the path is a symbolic link"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            result = context.services.file.information.is_symlink(path)
            return ActionResult(success=True, data={"is_symlink": result})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsFileAccessible(Action):
    name = "is_file_accessible"
    description = "Check read/write/execute permissions for the current user"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            perms = context.services.file.information.get_access_permissions(path)
            return ActionResult(success=True, data=perms)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))