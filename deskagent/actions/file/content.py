from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class ReadFile(Action):
    name = "read_file"
    description = "Read the entire content of a file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "encoding": {"type": "string", "required": False, "default": "utf-8"}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        enc = parameters.get('encoding', 'utf-8')
        try:
            content, size = context.services.file.content.read(path, encoding=enc)
            return ActionResult(success=True, data={
                "content": content,
                "size": size,
                "encoding": enc
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ReadTextFile(Action):
    name = "read_text_file"
    description = "Read a file specifically as text"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "encoding": {"type": "string", "required": False, "default": "utf-8"}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        enc = parameters.get('encoding', 'utf-8')
        try:
            content = context.services.file.content.read_text(path, encoding=enc)
            return ActionResult(success=True, data={"content": content})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ReadBinaryFile(Action):
    name = "read_binary_file"
    description = "Read a file as binary data (with size limit)"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "max_bytes": {"type": "integer", "required": False, "default": 1048576}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        max_b = parameters.get('max_bytes', 1048576)
        try:
            data, size = context.services.file.content.read_binary(path, max_bytes=max_b)
            return ActionResult(success=True, data={"content_base64": data, "size": size})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileContentPreview(Action):
    name = "get_file_content_preview"
    description = "Read only the first N characters or bytes of a file"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "max_length": {"type": "integer", "required": False, "default": 1000}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        limit = parameters.get('max_length', 1000)
        try:
            preview = context.services.file.content.get_preview(path, limit)
            return ActionResult(success=True, data={"preview": preview, "limit": limit})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class WriteFile(Action):
    name = "write_file"
    description = "Write raw content to a file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "content": {"type": "string", "required": True},
        "overwrite": {"type": "boolean", "required": False, "default": True}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        content = parameters.get('content')
        overwrite = parameters.get('overwrite', True)
        try:
            bytes_written = context.services.file.content.write(path, content, overwrite)
            return ActionResult(success=True, data={"written": True, "path": path, "bytes_written": bytes_written})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class WriteTextFile(Action):
    name = "write_text_file"
    description = "Write a text string to a file with specific encoding"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "content": {"type": "string", "required": True},
        "encoding": {"type": "string", "required": False, "default": "utf-8"}
    }

    def execute(self, context, parameters):
        path, content = parameters.get('path'), parameters.get('content')
        enc = parameters.get('encoding', 'utf-8')
        try:
            context.services.file.content.write_text(path, content, encoding=enc)
            return ActionResult(success=True, data={"path": path, "encoding": enc})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class AppendToFile(Action):
    name = "append_to_file"
    description = "Add content to the end of a file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "content": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        path, content = parameters.get('path'), parameters.get('content')
        try:
            context.services.file.content.append(path, content)
            return ActionResult(success=True, data={"appended": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class PrependToFile(Action):
    name = "prepend_to_file"
    description = "Add content to the beginning of a file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "content": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        path, content = parameters.get('path'), parameters.get('content')
        try:
            context.services.file.content.prepend(path, content)
            return ActionResult(success=True, data={"prepended": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class InsertIntoFile(Action):
    name = "insert_into_file"
    description = "Insert content at a specific position in the file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "content": {"type": "string", "required": True},
        "position": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        path, content, pos = parameters.get('path'), parameters.get('content'), parameters.get('position')
        try:
            context.services.file.content.insert(path, content, pos)
            return ActionResult(success=True, data={"inserted": True, "position": pos})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ReplaceInFile(Action):
    name = "replace_in_file"
    description = "Find and replace a string within a file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "old": {"type": "string", "required": True},
        "new": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        path, old, new = parameters.get('path'), parameters.get('old'), parameters.get('new')
        try:
            count = context.services.file.content.replace_string(path, old, new)
            return ActionResult(success=True, data={"replaced": True, "replacements": count})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ClearFile(Action):
    name = "clear_file"
    description = "Empty the content of a file without deleting it"
    category = ActionCategory.FILE
    risk_level = RiskLevel.HIGH
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.content.clear(path)
            return ActionResult(success=True, data={"cleared": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))