from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GroupWindows(Action):
    name = "group_windows"
    description = "Create a named group for a set of specific windows"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_ids": {"type": "list", "required": True, "description": "List of window IDs to include in the group"},
        "group_name": {"type": "string", "required": True, "description": "Name for the group (e.g., 'work', 'social')"}
    }

    def execute(self, context, parameters):
        win_ids = parameters.get('window_ids')
        group_name = parameters.get('group_name')
        try:
            context.services.window.groups.group(win_ids, group_name)
            return ActionResult(success=True, data={"group": group_name, "windows": win_ids})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class UngroupWindows(Action):
    name = "ungroup_windows"
    description = "Remove specific windows from their current group"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_ids": {"type": "list", "required": True, "description": "List of window IDs to remove from any group"}
    }

    def execute(self, context, parameters):
        win_ids = parameters.get('window_ids')
        try:
            context.services.window.groups.ungroup(win_ids)
            return ActionResult(success=True, data={"ungrouped": win_ids})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindowGroup(Action):
    name = "get_window_group"
    description = "Identify the group name a specific window belongs to"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            group_name = context.services.window.groups.get_group(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "group": group_name})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindowGroups(Action):
    name = "get_window_groups"
    description = "Get a list of all existing window groups and their windows"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            groups = context.services.window.groups.get_all_groups()
            return ActionResult(success=True, data={"groups": groups})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ActivateWindowGroup(Action):
    name = "activate_window_group"
    description = "Bring all windows belonging to a specific group to the foreground"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "group_name": {"type": "string", "required": True, "description": "Name of the group to activate"}
    }

    def execute(self, context, parameters):
        group_name = parameters.get('group_name')
        try:
            context.services.window.groups.activate(group_name)
            return ActionResult(success=True, data={"group": group_name, "activated": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ArrangeWindowGroup(Action):
    name = "arrange_window_group"
    description = "Arrange all windows in a group according to a specific layout"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "group_name": {"type": "string", "required": True},
        "layout": {"type": "string", "required": True, "enum": ["horizontal", "vertical", "tile", "cascade"]}
    }

    def execute(self, context, parameters):
        group_name = parameters.get('group_name')
        layout = parameters.get('layout')
        try:
            context.services.window.groups.arrange(group_name, layout)
            return ActionResult(success=True, data={"group": group_name, "layout": layout})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
