from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class MoveFiles(Action):
    name = "move_files"
    description = "Move multiple files to a single destination directory"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "files": {"type": "list", "required": True, "description": "List of file paths"},
        "destination": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        files = parameters.get('files')
        dest = parameters.get('destination')
        try:
            results = context.services.file.organization.move_batch(files, dest)
            return ActionResult(success=True, data={"moved_count": len(files), "results": results})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CopyFiles(Action):
    name = "copy_files"
    description = "Copy multiple files to a destination directory"
    category = ActionCategory.FILE
    parameters_schema = {
        "files": {"type": "list", "required": True},
        "destination": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        files, dest = parameters.get('files'), parameters.get('destination')
        try:
            results = context.services.file.organization.copy_batch(files, dest)
            return ActionResult(success=True, data={"copied_count": len(files), "results": results})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RenameFiles(Action):
    name = "rename_files"
    description = "Batch rename files in a directory using a template (e.g., 'photo_{index}.jpg')"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "pattern": {"type": "string", "required": True, "description": "Filter pattern like '*.jpg'"},
        "template": {"type": "string", "required": True, "description": "New name template with {index}"}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            renamed = context.services.file.organization.rename_batch(p['directory'], p['pattern'], p['template'])
            return ActionResult(success=True, data={"renamed_count": len(renamed), "files": renamed})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class DeleteFiles(Action):
    name = "delete_files"
    description = "Permanently delete multiple files"
    category = ActionCategory.FILE
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {
        "files": {"type": "list", "required": True}
    }

    def execute(self, context, parameters):
        files = parameters.get('files')
        try:
            context.services.file.organization.delete_batch(files)
            return ActionResult(success=True, data={"deleted_count": len(files)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class OrganizeFiles(Action):
    name = "organize_files"
    description = "Move files into folders based on custom rules (extensions to destination)"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "rules": {
            "type": "list",
            "required": True,
            "description": "List of {'extension': ['.pdf'], 'destination': 'path'} objects"
        }
    }

    def execute(self, context, parameters):
        d, rules = parameters.get('directory'), parameters.get('rules')
        try:
            report = context.services.file.organization.apply_rules(d, rules)
            return ActionResult(success=True, data={"organized": True, "report": report})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GroupFilesByType(Action):
    name = "group_files_by_type"
    description = "Automatically sort files into category folders (Images, Docs, Video, etc.)"
    category = ActionCategory.FILE
    parameters_schema = {"directory": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        d = parameters.get('directory')
        try:
            groups = context.services.file.organization.group_by_type(d)
            return ActionResult(success=True, data={"directory": d, "groups_created": list(groups.keys())})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GroupFilesByDate(Action):
    name = "group_files_by_date"
    description = "Sort files into nested folders by year and month"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "granularity": {"type": "string", "required": False, "default": "month", "enum": ["year", "month", "day"]}
    }

    def execute(self, context, parameters):
        d, g = parameters.get('directory'), parameters.get('granularity', 'month')
        try:
            context.services.file.organization.group_by_date(d, g)
            return ActionResult(success=True, data={"directory": d, "granularity": g})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SortFiles(Action):
    name = "sort_files"
    description = "Physically reorder files in a directory (by renaming with prefixes) or just retrieve sorted list"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "by": {"type": "string", "required": True, "enum": ["name", "size", "created", "modified", "extension"]},
        "order": {"type": "string", "required": False, "default": "asc", "enum": ["asc", "desc"]}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            sorted_list = context.services.file.organization.get_sorted_list(p['directory'], p['by'], p['order'])
            return ActionResult(success=True, data={"files": sorted_list})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FlattenDirectory(Action):
    name = "flatten_directory"
    description = "Move all files from subdirectories into the root of the specified directory"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "conflict_strategy": {"type": "string", "required": False, "default": "rename", "enum": ["rename", "overwrite", "skip"]}
    }

    def execute(self, context, parameters):
        d, strategy = parameters.get('directory'), parameters.get('conflict_strategy', 'rename')
        try:
            count = context.services.file.organization.flatten(d, strategy)
            return ActionResult(success=True, data={"files_moved": count, "strategy": strategy})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))