from __future__ import annotations

from deskagent.actions.accessibility.common import (
    IDENTIFIER_SCHEMA,
    QUERY_SCHEMA,
    AccessibilityAction,
)
from deskagent.actions.types import ActionResult
from deskagent.perception.accessibility import (
    AccessibilityObserver,
    serialize_element,
    serialize_match,
)

TIMEOUT_SCHEMA = {
    "timeout": {
        "type": "float",
        "required": False,
        "default": 10,
        "minimum": 0.1,
        "maximum": 300,
    },
    "poll_interval": {
        "type": "float",
        "required": False,
        "default": 0.2,
        "minimum": 0.05,
        "maximum": 5,
    },
}


class _WaitAction(AccessibilityAction):
    discoverable = False

    def __init__(self):
        self.observer = None

    def make_observer(self, context, parameters):
        self.observer = AccessibilityObserver(
            self.client(context), parameters.get("poll_interval", 0.2)
        )
        return self.observer

    def cancel(self):
        if self.observer:
            self.observer.cancel()


class WaitForUIElement(_WaitAction):
    name = "wait_for_ui_element"
    description = "Wait until a UI element matching semantic filters appears"
    discoverable = True
    parameters_schema = {**QUERY_SCHEMA, **TIMEOUT_SCHEMA}

    def execute(self, context, parameters):
        try:
            match = self.make_observer(context, parameters).element(
                self.query(parameters), parameters.get("timeout", 10)
            )
            return ActionResult(success=True, data=serialize_match(match))
        except Exception as exc:
            return self.failure(exc)


class WaitForUIElementDisappear(_WaitAction):
    name = "wait_for_ui_element_disappear"
    description = "Wait until no UI element matching semantic filters remains"
    discoverable = True
    parameters_schema = {**QUERY_SCHEMA, **TIMEOUT_SCHEMA}

    def execute(self, context, parameters):
        try:
            disappeared = self.make_observer(context, parameters).disappearance(
                self.query(parameters), parameters.get("timeout", 10)
            )
            return ActionResult(success=True, data={"disappeared": disappeared})
        except Exception as exc:
            return self.failure(exc)


class WaitForUIElementEnabled(_WaitAction):
    name = "wait_for_ui_element_enabled"
    description = "Wait until a known UI element becomes enabled"
    discoverable = True
    parameters_schema = {**IDENTIFIER_SCHEMA, **TIMEOUT_SCHEMA}

    def execute(self, context, parameters):
        try:
            element = self.make_observer(context, parameters).state(
                parameters["element"],
                lambda item: item.enabled,
                parameters.get("timeout", 10),
                "UI element to become enabled",
            )
            return self.success_element(element)
        except Exception as exc:
            return self.failure(exc)


class WaitForUIValue(_WaitAction):
    name = "wait_for_ui_value"
    description = "Wait until a known UI element has the expected value"
    discoverable = True
    parameters_schema = {
        **IDENTIFIER_SCHEMA,
        "value": {"required": True},
        **TIMEOUT_SCHEMA,
    }

    def execute(self, context, parameters):
        try:
            expected = parameters["value"]
            element = self.make_observer(context, parameters).state(
                parameters["element"],
                lambda item: item.value == expected,
                parameters.get("timeout", 10),
                f"UI value {expected!r}",
            )
            return self.success_element(element)
        except Exception as exc:
            return self.failure(exc)


class VerifyUIElementState(AccessibilityAction):
    name = "verify_ui_element_state"
    description = (
        "Verify enabled, focused, selected, visible or value state of a UI element"
    )
    parameters_schema = {
        **IDENTIFIER_SCHEMA,
        "enabled": {"type": "boolean", "required": False},
        "focused": {"type": "boolean", "required": False},
        "selected": {"type": "boolean", "required": False},
        "visible": {"type": "boolean", "required": False},
        "value": {"required": False},
    }

    def execute(self, context, parameters):
        try:
            element = self.client(context).refresh(parameters["element"])
            expected = {
                key: parameters[key]
                for key in ("enabled", "focused", "selected", "visible", "value")
                if key in parameters
            }
            actual = {key: getattr(element, key) for key in expected}
            mismatches = {
                key: {"expected": expected[key], "actual": actual[key]}
                for key in expected
                if expected[key] != actual[key]
            }
            return ActionResult(
                success=True,
                data={
                    "verified": not mismatches,
                    "expected": expected,
                    "actual": actual,
                    "mismatches": mismatches,
                    "element": serialize_element(element, include_children=False),
                },
            )
        except Exception as exc:
            return self.failure(exc)
