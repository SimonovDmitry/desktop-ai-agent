from __future__ import annotations

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.perception.accessibility import (
    ElementQuery,
    serialize_element,
    serialize_match,
)

QUERY_SCHEMA = {
    "application": {"type": "string", "required": False},
    "window": {"type": "string", "required": False},
    "role": {"type": "string", "required": False},
    "text": {"type": "string", "required": False},
    "locator": {"type": "string", "required": False},
    "visible_only": {"type": "boolean", "required": False, "default": False},
    "enabled_only": {"type": "boolean", "required": False, "default": False},
    "fuzzy": {"type": "boolean", "required": False, "default": False},
    "minimum_confidence": {
        "type": "float",
        "required": False,
        "default": 0.6,
        "minimum": 0,
        "maximum": 1,
    },
}

TREE_LIMIT_SCHEMA = {
    "max_depth": {
        "type": "integer",
        "required": False,
        "default": 12,
        "minimum": 0,
        "maximum": 50,
    },
    "max_nodes": {
        "type": "integer",
        "required": False,
        "default": 2000,
        "minimum": 1,
        "maximum": 10000,
    },
}

IDENTIFIER_SCHEMA = {
    "element": {
        "type": "string",
        "required": True,
        "description": "Element id or stable ax:// locator returned by a query",
    },
}


class AccessibilityAction(Action):
    category = ActionCategory.ACCESSIBILITY
    risk_level = RiskLevel.LOW
    required_permissions = ("accessibility",)

    @staticmethod
    def client(context):
        client = getattr(context.services, "accessibility", None)
        if client is None:
            raise RuntimeError("Accessibility service is not configured")
        return client

    @staticmethod
    def query(parameters, **overrides):
        values = {key: parameters.get(key) for key in QUERY_SCHEMA if key in parameters}
        values.update(overrides)
        return ElementQuery(**values)

    @staticmethod
    def success_element(element, **extra):
        return ActionResult(
            success=True, data={"element": serialize_element(element), **extra}
        )

    @staticmethod
    def failure(exc):
        if isinstance(exc, TimeoutError):
            code = "TIMEOUT"
        elif exc.__class__.__name__ == "ElementNotFoundError":
            code = "ELEMENT_NOT_FOUND"
        elif exc.__class__.__name__ == "AccessibilityPermissionError":
            code = "PERMISSION_DENIED"
        elif isinstance(exc, InterruptedError):
            code = "ACTION_CANCELLED"
        else:
            code = "ACCESSIBILITY_ERROR"
        return ActionResult(success=False, error=str(exc), error_code=code)


def serialize_matches(matches):
    return [serialize_match(match) for match in matches]
