from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetWindowParent(Action):
    name = "get_window_parent"
    description = "Get the parent window ID for a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            parent_id = context.services.window.hierarchy.get_parent(win_id)
            return ActionResult(success=True, data={"parent_window_id": parent_id})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindowChildren(Action):
    name = "get_window_children"
    description = "Get a list of all child windows belonging to a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            children = context.services.window.hierarchy.get_children(win_id)
            return ActionResult(success=True, data={"children": children})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindowOwner(Action):
    name = "get_window_owner"
    description = "Identify the application and process that owns a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            owner_info = context.services.window.hierarchy.get_owner(win_id)
            return ActionResult(success=True, data=owner_info)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetApplicationWindows(Action):
    name = "get_application_windows"
    description = "Get a list of all windows opened by a specific application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "application": {"type": "string", "required": True, "description": "Name of the application"}
    }

    def execute(self, context, parameters):
        app_name = parameters.get('application')
        try:
            windows = context.services.window.hierarchy.get_app_windows(app_name)
            return ActionResult(success=True, data={"windows": windows})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindowHierarchy(Action):
    name = "get_window_hierarchy"
    description = "Get a full tree structure of a window and its nested children"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            tree = context.services.window.hierarchy.get_hierarchy(win_id)
            return ActionResult(success=True, data=tree)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
