import time

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


def _get_keyboard(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "keyboard"):
        return context.services.system.keyboard
    if hasattr(context.services, "input") and hasattr(context.services.input, "shortcuts"):
        return context.services.input.shortcuts
    return getattr(context.services, "keyboard", None)


def _get_focus(context):
    if hasattr(context.services, "application") and hasattr(context.services.application, "focus"):
        return context.services.application.focus
    return None


class PressShortcut(Action):
    name = "press_shortcut"
    description = "Perform a key combination (e.g., 'cmd+c', 'ctrl+alt+delete')"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {"shortcut": {"type": "string", "required": True, "description": "Combination string"}}

    def execute(self, context, parameters):
        shortcut = parameters.get("shortcut")
        if not shortcut:
            return ActionResult(success=False, error="Missing shortcut parameter", error_code="MISSING_PARAM")
        try:
            _get_keyboard(context).press_shortcut(shortcut)
            return ActionResult(success=True, data={"shortcut": shortcut, "executed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ExecuteShortcutSequence(Action):
    name = "execute_shortcut_sequence"
    description = "Perform multiple shortcuts in a sequence with optional delays"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "shortcuts": {"type": "list", "required": True, "description": "List of strings like ['cmd+a', 'cmd+c']"},
        "delay": {"type": "float", "required": False, "default": 0.1},
    }

    def execute(self, context, parameters):
        shortcuts = parameters.get("shortcuts")
        delay = parameters.get("delay", 0.1)
        if not isinstance(shortcuts, list):
            return ActionResult(success=False, error="Shortcuts must be a list", error_code="INVALID_INPUT")

        try:
            kb = _get_keyboard(context)
            for s in shortcuts:
                kb.press_shortcut(s)
                time.sleep(delay)
            return ActionResult(success=True, data={"executed": len(shortcuts), "completed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class Copy(Action):
    name = "copy"
    description = "Copy current selection to clipboard using system shortcut"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            _get_keyboard(context).copy()
            return ActionResult(success=True, data={"copied": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class Paste(Action):
    name = "paste"
    description = "Paste from clipboard using system shortcut"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            _get_keyboard(context).paste()
            return ActionResult(success=True, data={"pasted": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class Cut(Action):
    name = "cut"
    description = "Cut current selection using system shortcut"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            _get_keyboard(context).cut()
            return ActionResult(success=True, data={"cut": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class Undo(Action):
    name = "undo"
    description = "Undo the last action"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            _get_keyboard(context).undo()
            return ActionResult(success=True, data={"undone": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class Redo(Action):
    name = "redo"
    description = "Redo the last undone action"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            _get_keyboard(context).redo()
            return ActionResult(success=True, data={"redone": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class Save(Action):
    name = "save"
    description = "Save current document/file"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            _get_keyboard(context).save()
            return ActionResult(success=True, data={"saved": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SaveAs(Action):
    name = "save_as"
    description = "Save current document under another path"
    category = ActionCategory.INPUT
    parameters_schema = {"path": {"type": "string", "required": False}}

    def execute(self, context, parameters):
        path = parameters.get("path")
        try:
            _get_keyboard(context).save_as(path)
            return ActionResult(success=True, data={"saved": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class Find(Action):
    name = "find"
    description = "Open find dialog and search for text"
    category = ActionCategory.SYSTEM
    parameters_schema = {"text": {"type": "string", "required": True, "description": "Text to search for"}}

    def execute(self, context, parameters):
        text = parameters.get("text")
        try:
            kb = _get_keyboard(context)
            kb.press_shortcut("cmd+f")
            time.sleep(0.2)
            kb.type(text)
            return ActionResult(success=True, data={"search": text, "executed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class Close(Action):
    name = "close"
    description = "Close the current window or tab"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            _get_keyboard(context).close()
            return ActionResult(success=True, data={"closed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class Quit(Action):
    name = "quit"
    description = "Quit the current application"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            _get_keyboard(context).quit()
            return ActionResult(success=True, data={"quit": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SwitchApplication(Action):
    name = "switch_application"
    description = "Switch focus to another application"
    category = ActionCategory.SYSTEM
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        app_name = parameters.get("application")
        try:
            focus = _get_focus(context)
            if focus and hasattr(focus, "activate"):
                focus.activate(app_name)
            else:
                kb = _get_keyboard(context)
                if hasattr(kb, "switch_application"):
                    kb.switch_application(app_name)
            return ActionResult(success=True, data={"application": app_name, "switched": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))
