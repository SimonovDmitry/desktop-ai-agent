from deskagent.actions.accessibility.common import (
    IDENTIFIER_SCHEMA,
    QUERY_SCHEMA,
    TREE_LIMIT_SCHEMA,
    AccessibilityAction,
    serialize_matches,
)
from deskagent.actions.types import ActionResult
from deskagent.perception.accessibility import serialize_element, serialize_match
from deskagent.perception.accessibility.serializer import json_safe


class GetAccessibilityStatus(AccessibilityAction):
    name = "get_accessibility_status"
    description = "Check whether macOS Accessibility API is supported and trusted"
    required_permissions = ()
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            return ActionResult(success=True, data=self.client(context).status())
        except Exception as exc:
            return self.failure(exc)


class RequestAccessibilityPermission(AccessibilityAction):
    name = "request_accessibility_permission"
    description = "Ask macOS to display the Accessibility permission prompt"
    required_permissions = ()
    parameters_schema = {
        "prompt": {"type": "boolean", "required": False, "default": True}
    }

    def execute(self, context, parameters):
        try:
            return ActionResult(
                success=True,
                data=self.client(context).request_permission(
                    parameters.get("prompt", True)
                ),
            )
        except Exception as exc:
            return self.failure(exc)


class GetFocusedUIElement(AccessibilityAction):
    name = "get_focused_ui_element"
    description = "Get the UI element that currently owns keyboard focus"
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            return self.success_element(self.client(context).focused_element())
        except Exception as exc:
            return self.failure(exc)


class GetApplicationUITree(AccessibilityAction):
    name = "get_application_ui_tree"
    description = "Read a bounded semantic accessibility tree for an application"
    parameters_schema = {
        "application": {"type": "string", "required": True},
        **TREE_LIMIT_SCHEMA,
    }

    def execute(self, context, parameters):
        try:
            root = self.client(context).application_tree(
                parameters["application"],
                parameters.get("max_depth"),
                parameters.get("max_nodes"),
            )
            return ActionResult(success=True, data={"root": serialize_element(root)})
        except Exception as exc:
            return self.failure(exc)


class GetWindowUITree(AccessibilityAction):
    name = "get_window_ui_tree"
    description = "Read a bounded semantic accessibility tree for an application window"
    parameters_schema = {
        "application": {"type": "string", "required": True},
        "window": {"type": "string", "required": False},
        **TREE_LIMIT_SCHEMA,
    }

    def execute(self, context, parameters):
        try:
            root = self.client(context).window_tree(
                parameters["application"],
                parameters.get("window"),
                parameters.get("max_depth"),
                parameters.get("max_nodes"),
            )
            return ActionResult(success=True, data={"root": serialize_element(root)})
        except Exception as exc:
            return self.failure(exc)


class ListUIElements(AccessibilityAction):
    name = "list_ui_elements"
    description = "List flattened UI elements matching optional semantic filters"
    parameters_schema = {
        **QUERY_SCHEMA,
        **TREE_LIMIT_SCHEMA,
        "limit": {
            "type": "integer",
            "required": False,
            "default": 100,
            "minimum": 1,
            "maximum": 1000,
        },
    }

    def execute(self, context, parameters):
        try:
            matches = self.client(context).find_all(
                self.query(parameters),
                parameters.get("limit", 100),
                parameters.get("max_depth"),
                parameters.get("max_nodes"),
            )
            return ActionResult(
                success=True,
                data={"elements": serialize_matches(matches), "count": len(matches)},
            )
        except Exception as exc:
            return self.failure(exc)


class GetUIElement(AccessibilityAction):
    name = "get_ui_element"
    description = "Resolve a previously returned UI element id or locator"
    parameters_schema = IDENTIFIER_SCHEMA

    def execute(self, context, parameters):
        try:
            return self.success_element(self.client(context).get(parameters["element"]))
        except Exception as exc:
            return self.failure(exc)


class FindUIElement(AccessibilityAction):
    name = "find_ui_element"
    description = (
        "Find the best UI element using role, text, visibility and fuzzy matching"
    )
    parameters_schema = QUERY_SCHEMA

    def execute(self, context, parameters):
        try:
            match = self.client(context).find(self.query(parameters))
            if match is None:
                return ActionResult(
                    success=False,
                    error="No UI element matched the query",
                    error_code="ELEMENT_NOT_FOUND",
                )
            return ActionResult(success=True, data=serialize_match(match))
        except Exception as exc:
            return self.failure(exc)


class FindUIElementsByText(AccessibilityAction):
    name = "find_ui_elements_by_text"
    description = "Find UI elements by title, value, description, help or identifier"
    parameters_schema = {
        **QUERY_SCHEMA,
        "text": {"type": "string", "required": True},
        "limit": {
            "type": "integer",
            "required": False,
            "default": 20,
            "minimum": 1,
            "maximum": 1000,
        },
    }

    def execute(self, context, parameters):
        try:
            matches = self.client(context).find_all(
                self.query(parameters), parameters.get("limit", 20)
            )
            return ActionResult(
                success=True,
                data={"elements": serialize_matches(matches), "count": len(matches)},
            )
        except Exception as exc:
            return self.failure(exc)


class FindUIElementsByRole(AccessibilityAction):
    name = "find_ui_elements_by_role"
    description = "Find UI elements by an AX role or a friendly role alias"
    parameters_schema = {
        **QUERY_SCHEMA,
        "role": {"type": "string", "required": True},
        "limit": {
            "type": "integer",
            "required": False,
            "default": 100,
            "minimum": 1,
            "maximum": 1000,
        },
    }

    def execute(self, context, parameters):
        try:
            matches = self.client(context).find_all(
                self.query(parameters), parameters.get("limit", 100)
            )
            return ActionResult(
                success=True,
                data={"elements": serialize_matches(matches), "count": len(matches)},
            )
        except Exception as exc:
            return self.failure(exc)


class _ElementPropertyAction(AccessibilityAction):
    discoverable = False
    parameters_schema = IDENTIFIER_SCHEMA
    property_name = ""

    def execute(self, context, parameters):
        try:
            element = self.client(context).refresh(parameters["element"])
            value = getattr(element, self.property_name)
            if self.property_name == "bounds":
                value = {
                    "position": element.position,
                    "size": element.size,
                    "visible": element.visible,
                }
            return ActionResult(
                success=True,
                data={
                    self.property_name: json_safe(value),
                    "id": element.id,
                    "locator": element.locator,
                },
            )
        except Exception as exc:
            return self.failure(exc)


class GetUIElementActions(_ElementPropertyAction):
    name = "get_ui_element_actions"
    description = "Get the native AX actions supported by a UI element"
    property_name = "actions"
    discoverable = True


class GetUIElementBounds(_ElementPropertyAction):
    name = "get_ui_element_bounds"
    description = "Get position, size and visibility of a UI element"
    property_name = "bounds"
    discoverable = True


class GetUIElementValue(_ElementPropertyAction):
    name = "get_ui_element_value"
    description = "Get the current value of a UI element"
    property_name = "value"
    discoverable = True
