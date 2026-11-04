from deskagent.actions.accessibility.common import (
    IDENTIFIER_SCHEMA,
    AccessibilityAction,
)
from deskagent.actions.types import ActionResult, RiskLevel
from deskagent.perception.accessibility import serialize_element


class _PerformAction(AccessibilityAction):
    discoverable = False
    ax_action = ""
    parameters_schema = IDENTIFIER_SCHEMA

    def execute(self, context, parameters):
        try:
            element = self.client(context).perform(
                parameters["element"], self.ax_action
            )
            return ActionResult(
                success=True,
                data={
                    "performed_action": self.ax_action,
                    "element": serialize_element(element),
                },
            )
        except Exception as exc:
            return self.failure(exc)


class PressUIElement(_PerformAction):
    name = "press_ui_element"
    description = "Press or activate a UI element using AXPress"
    ax_action = "AXPress"
    discoverable = True


class FocusUIElement(AccessibilityAction):
    name = "focus_ui_element"
    description = "Move keyboard focus to a UI element"
    parameters_schema = IDENTIFIER_SCHEMA

    def execute(self, context, parameters):
        try:
            return self.success_element(
                self.client(context).set_focused(parameters["element"])
            )
        except Exception as exc:
            return self.failure(exc)


class SetUIElementValue(AccessibilityAction):
    name = "set_ui_element_value"
    description = "Set the AXValue of an editable UI element"
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {**IDENTIFIER_SCHEMA, "value": {"required": True}}

    def execute(self, context, parameters):
        try:
            return self.success_element(
                self.client(context).set_value(
                    parameters["element"], parameters["value"]
                )
            )
        except Exception as exc:
            return self.failure(exc)


class SelectUIElement(AccessibilityAction):
    name = "select_ui_element"
    description = "Set an element's AXSelected state"
    parameters_schema = {
        **IDENTIFIER_SCHEMA,
        "selected": {"type": "boolean", "required": False, "default": True},
    }

    def execute(self, context, parameters):
        try:
            element = self.client(context).set_selected(
                parameters["element"], parameters.get("selected", True)
            )
            return self.success_element(element)
        except Exception as exc:
            return self.failure(exc)


class ExpandUIElement(AccessibilityAction):
    name = "expand_ui_element"
    description = "Expand a disclosure, row or hierarchical UI element"
    parameters_schema = IDENTIFIER_SCHEMA

    def execute(self, context, parameters):
        try:
            return self.success_element(
                self.client(context).set_expanded(parameters["element"], True)
            )
        except Exception as exc:
            return self.failure(exc)


class CollapseUIElement(AccessibilityAction):
    name = "collapse_ui_element"
    description = "Collapse a disclosure, row or hierarchical UI element"
    parameters_schema = IDENTIFIER_SCHEMA

    def execute(self, context, parameters):
        try:
            return self.success_element(
                self.client(context).set_expanded(parameters["element"], False)
            )
        except Exception as exc:
            return self.failure(exc)


class IncrementUIElement(_PerformAction):
    name = "increment_ui_element"
    description = "Increment a stepper, slider or other numeric UI element"
    ax_action = "AXIncrement"
    discoverable = True


class DecrementUIElement(_PerformAction):
    name = "decrement_ui_element"
    description = "Decrement a stepper, slider or other numeric UI element"
    ax_action = "AXDecrement"
    discoverable = True


class ScrollUIElement(AccessibilityAction):
    name = "scroll_ui_element"
    description = "Scroll a UI element in a semantic direction"
    parameters_schema = {
        **IDENTIFIER_SCHEMA,
        "direction": {
            "type": "string",
            "required": True,
            "enum": ["up", "down", "left", "right"],
        },
        "amount": {
            "type": "float",
            "required": False,
            "default": 0.8,
            "minimum": 0.01,
            "maximum": 1.0,
        },
    }

    def execute(self, context, parameters):
        try:
            direction = parameters["direction"]
            element = self.client(context).scroll(
                parameters["element"], direction, parameters.get("amount", 0.8)
            )
            return ActionResult(
                success=True,
                data={
                    "direction": direction,
                    "element": serialize_element(element),
                },
            )
        except Exception as exc:
            return self.failure(exc)


class ShowUIElementMenu(_PerformAction):
    name = "show_ui_element_menu"
    description = "Open the contextual menu for a UI element"
    ax_action = "AXShowMenu"
    discoverable = True


class PerformUIElementAction(AccessibilityAction):
    name = "perform_ui_element_action"
    description = "Perform an explicitly named native action supported by a UI element"
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        **IDENTIFIER_SCHEMA,
        "ax_action": {"type": "string", "required": True},
    }

    def execute(self, context, parameters):
        try:
            element = self.client(context).get(parameters["element"])
            action = parameters["ax_action"]
            if action not in element.actions:
                return ActionResult(
                    success=False,
                    error=f"Unsupported action {action}; available: {element.actions}",
                    error_code="UNSUPPORTED_ACTION",
                )
            updated = self.client(context).perform(element.id, action)
            return ActionResult(
                success=True,
                data={
                    "performed_action": action,
                    "element": serialize_element(updated),
                },
            )
        except Exception as exc:
            return self.failure(exc)
