from deskagent.core.action import Action, ActionResult, ActionCategory, RiskLevel


class ActivateWindow(Action):
    name = "activate_window"
    description = "Make a specific window active and give it focus"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {
            "type": "integer",
            "required": True,
            "description": "ID of the window to activate"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.focus.activate(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "active": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class FocusWindow(Action):
    name = "focus_window"
    description = "Focus on a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {
            "type": "integer",
            "required": True,
            "description": "ID of the window to focus"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.focus.focus(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "focused": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class BringWindowToFront(Action):
    name = "bring_window_to_front"
    description = "Bring a window to the front of all other windows"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {
            "type": "integer",
            "required": True,
            "description": "ID of the window to bring to front"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.focus.bring_to_front(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "front": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SendWindowToBack(Action):
    name = "send_window_to_back"
    description = "Send a window behind all other windows"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {
            "type": "integer",
            "required": True,
            "description": "ID of the window to send to back"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.focus.send_to_back(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "back": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MinimizeWindow(Action):
    name = "minimize_window"
    description = "Minimize a specific window to the dock or taskbar"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {
            "type": "integer",
            "required": True,
            "description": "ID of the window to minimize"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.focus.minimize(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "state": "minimized"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class RestoreWindow(Action):
    name = "restore_window"
    description = "Restore a minimized or maximized window to its normal state"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {
            "type": "integer",
            "required": True,
            "description": "ID of the window to restore"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.focus.restore(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "state": "normal"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MaximizeWindow(Action):
    name = "maximize_window"
    description = "Maximize a window to fill the screen"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {
            "type": "integer",
            "required": True,
            "description": "ID of the window to maximize"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.focus.maximize(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "state": "maximized"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class UnmaximizeWindow(Action):
    name = "unmaximize_window"
    description = "Return a maximized window to its normal size"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {
            "type": "integer",
            "required": True,
            "description": "ID of the window to unmaximize"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            # Логически unmaximize это и есть restore
            context.services.window.focus.restore(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "state": "normal"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ToggleWindowMaximize(Action):
    name = "toggle_window_maximize"
    description = "Switch between maximized and normal window states"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {
            "type": "integer",
            "required": True,
            "description": "ID of the window to toggle"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            new_state = context.services.window.focus.toggle_maximize(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "state": new_state})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")