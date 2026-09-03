from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory
import time


class PressShortcut(Action):
    name = "press_shortcut"
    description = "Perform a key combination (e.g., 'cmd+c', 'ctrl+alt+delete')"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "shortcut": {"type": "string", "required": True, "description": "Combination string"}
    }

    def execute(self, context, parameters):
        shortcut = parameters.get('shortcut')
        if not shortcut:
            return ActionResult(success=False, error="Missing shortcut parameter", error_code="MISSING_PARAM")
        try:
            context.services.system.keyboard.press_shortcut(shortcut)
            return ActionResult(success=True, data={"shortcut": shortcut, "executed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ExecuteShortcutSequence(Action):
    name = "execute_shortcut_sequence"
    description = "Perform multiple shortcuts in a sequence with optional delays"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "shortcuts": {"type": "list", "required": True, "description": "List of strings like ['cmd+a', 'cmd+c']"},
        "delay": {"type": "float", "required": False, "default": 0.1}
    }

    def execute(self, context, parameters):
        shortcuts = parameters.get('shortcuts')
        delay = parameters.get('delay', 0.1)
        if not isinstance(shortcuts, list):
            return ActionResult(success=False, error="Shortcuts must be a list", error_code="INVALID_INPUT")

        try:
            for s in shortcuts:
                context.services.system.keyboard.press_shortcut(s)
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
            context.services.system.keyboard.copy()
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
            context.services.system.keyboard.paste()
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
            context.services.system.keyboard.cut()
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
            context.services.system.keyboard.undo()
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
            context.services.system.keyboard.redo()
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
            context.services.system.keyboard.save()
            return ActionResult(success=True, data={"saved": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class Find(Action):
    name = "find"
    description = "Open find dialog and search for text"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "text": {"type": "string", "required": True, "description": "Text to search for"}
    }

    def execute(self, context, parameters):
        text = parameters.get('text')
        try:
            context.services.system.keyboard.press_shortcut("cmd+f")
            time.sleep(0.2)
            context.services.system.keyboard.type(text)
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
            context.services.system.keyboard.close()
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
            context.services.system.keyboard.quit()
            return ActionResult(success=True, data={"quit": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SwitchApplication(Action):
    name = "switch_application"
    description = "Switch focus to another application"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "application": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        app_name = parameters.get('application')
        try:
            context.services.application.focus.activate(app_name)
            return ActionResult(success=True, data={"application": app_name, "switched": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))