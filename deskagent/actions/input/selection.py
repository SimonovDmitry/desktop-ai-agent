from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class SelectAllText(Action):
    name = "select_all_text"
    description = "Select all text or elements in the current context"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.select_all()
            return ActionResult(success=True, data={"selected": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SelectText(Action):
    name = "select_text"
    description = "Select a range of text between two positions"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "start": {"type": "integer", "required": True, "description": "Start character index"},
        "end": {"type": "integer", "required": True, "description": "End character index"}
    }

    def execute(self, context, parameters):
        start = parameters.get('start')
        end = parameters.get('end')
        if start is None or end is None:
            return ActionResult(success=False, error="Start and end positions required", error_code="MISSING_PARAM")

        try:
            context.services.system.keyboard.select_range(start, end)
            return ActionResult(success=True, data={"start": start, "end": end, "selected": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SelectWord(Action):
    name = "select_word"
    description = "Select the word currently under or nearest to the cursor"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.select_word()
            return ActionResult(success=True, data={"selected": True, "unit": "word"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SelectLine(Action):
    name = "select_line"
    description = "Select the entire line where the cursor is currently placed"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.select_line()
            return ActionResult(success=True, data={"selected": True, "unit": "line"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SelectToStart(Action):
    name = "select_to_start"
    description = "Extend selection from the current position to the start of the line or document"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "scope": {
            "type": "string",
            "required": False,
            "default": "line",
            "enum": ["line", "document"]
        }
    }

    def execute(self, context, parameters):
        scope = parameters.get('scope', 'line')
        try:
            context.services.system.keyboard.select_to_start(scope)
            return ActionResult(success=True, data={"scope": scope, "extended": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SelectToEnd(Action):
    name = "select_to_end"
    description = "Extend selection from the current position to the end of the line or document"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "scope": {
            "type": "string",
            "required": False,
            "default": "line",
            "enum": ["line", "document"]
        }
    }

    def execute(self, context, parameters):
        scope = parameters.get('scope', 'line')
        try:
            context.services.system.keyboard.select_to_end(scope)
            return ActionResult(success=True, data={"scope": scope, "extended": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ExtendSelection(Action):
    name = "extend_selection"
    description = "Extend the current selection in a specific direction"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "direction": {"type": "string", "required": True, "enum": ["up", "down", "left", "right"]},
        "amount": {"type": "integer", "required": True, "description": "Number of units to extend"},
        "unit": {"type": "string", "required": True, "enum": ["character", "word", "line"]}
    }

    def execute(self, context, parameters):
        p = parameters
        if any(p.get(k) is None for k in ["direction", "amount", "unit"]):
            return ActionResult(success=False, error="Missing required parameters", error_code="MISSING_PARAM")

        try:
            context.services.system.keyboard.extend_selection(p['direction'], p['amount'], p['unit'])
            return ActionResult(success=True,
                                data={"direction": p['direction'], "amount": p['amount'], "unit": p['unit']})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ClearSelection(Action):
    name = "clear_selection"
    description = "Deselect any currently selected text or items"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.clear_selection()
            return ActionResult(success=True, data={"cleared": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))