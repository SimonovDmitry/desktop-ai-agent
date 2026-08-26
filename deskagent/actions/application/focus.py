from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class ActivateApplication(Action):
    name = "activate_application"
    description = "Bring an application to the foreground and give it focus"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "application": {
            "type": "string",
            "required": True,
            "description": "Name of the application to activate"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            context.services.application.focus.activate(app_name)
            return ActionResult(success=True, data={"application": app_name, "active": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class HideApplication(Action):
    name = "hide_application"
    description = "Hide all windows of a specific application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            context.services.application.focus.hide(app_name)
            return ActionResult(success=True, data={"application": app_name, "hidden": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ShowApplication(Action):
    name = "show_application"
    description = "Unhide or show a specific application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            context.services.application.focus.show(app_name)
            return ActionResult(success=True, data={"application": app_name, "visible": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MinimizeApplication(Action):
    name = "minimize_application"
    description = "Minimize all windows of a specific application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            context.services.application.focus.minimize(app_name)
            return ActionResult(success=True, data={"application": app_name, "minimized": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RestoreApplication(Action):
    name = "restore_application"
    description = "Restore application windows from minimized state"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            context.services.application.focus.restore(app_name)
            return ActionResult(success=True, data={"application": app_name, "restored": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class BringApplicationToFront(Action):
    name = "bring_application_to_front"
    description = "Bring application windows to the top of the Z-order"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            context.services.application.focus.bring_to_front(app_name)
            return ActionResult(success=True, data={"application": app_name, "front": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationVisibility(Action):
    name = "get_application_visibility"
    description = "Check if the application is currently visible on screen"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            is_visible = context.services.application.focus.get_visibility(app_name)
            return ActionResult(success=True, data={
                "visible": is_visible,
                "hidden": not is_visible
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationFocusState(Action):
    name = "get_application_focus_state"
    description = "Check if the application is currently the focused (active) one"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            is_focused = context.services.application.focus.is_focused(app_name)
            return ActionResult(success=True, data={"focused": is_focused})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))