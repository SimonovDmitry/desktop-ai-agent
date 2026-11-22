"""Higher-level actions built on the existing macOS accessibility client."""

from __future__ import annotations

import hashlib
import json
import threading
import time

from deskagent.actions.accessibility.common import QUERY_SCHEMA, AccessibilityAction
from deskagent.actions.accessibility.target_resolution import resolve
from deskagent.actions.accessibility.safety import redact_secure_values
from deskagent.actions.types import ActionResult, RiskLevel
from deskagent.core.permissions import PermissionManager
from deskagent.perception.accessibility import serialize_element, serialize_match


TARGET_SCHEMA = {**QUERY_SCHEMA, "backend": {
    "type": "string", "required": False, "default": "auto",
    "enum": ["auto", "accessibility", "dom", "ocr"],
}}


def _find_unique(client, parameters):
    if not any(parameters.get(key) for key in ("text", "role", "locator")):
        raise ValueError("At least one of text, role or locator is required")
    query = AccessibilityAction.query(parameters, visible_only=True, enabled_only=True)
    matches = client.find_all(query, limit=2)
    if not matches:
        raise LookupError("Target was not found")
    if len(matches) > 1 and matches[0].confidence == matches[1].confidence:
        raise ValueError("Target is ambiguous; specify a role, window or locator")
    return matches[0]


def _snapshot(client, application=None, window=None):
    root = client.window_tree(application, window, max_depth=8, max_nodes=1000) if window else client.application_tree(
        application, max_depth=8, max_nodes=1000
    )
    data = serialize_element(root)
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return {"digest": hashlib.sha256(payload.encode()).hexdigest(), "application": application, "window": window}


class FindTarget(AccessibilityAction):
    name = "find_target"
    description = "Find a unique visible target through Accessibility, DOM or screen text"
    parameters_schema = TARGET_SCHEMA
    required_permissions = ()

    def execute(self, context, parameters):
        try:
            target = resolve(context, parameters, self.client(context), _find_unique)
            if target["source"] == "accessibility":
                return ActionResult(True, redact_secure_values({
                    "source": "accessibility", **serialize_match(target["match"]),
                }))
            return ActionResult(True, target)
        except Exception as exc:
            return self.failure(exc)


class ClickTarget(AccessibilityAction):
    name = "click_target"
    description = "Find and press a unique UI target through Accessibility, DOM or screen text"
    risk_level = RiskLevel.MEDIUM
    parameters_schema = TARGET_SCHEMA
    required_permissions = ()

    def execute(self, context, parameters):
        try:
            client = self.client(context)
            target = resolve(context, parameters, client, _find_unique)
            if target["source"] == "accessibility":
                element = target["match"].element
                if "AXPress" not in element.actions:
                    raise ValueError("Target does not support AXPress")
                before = redact_secure_values(serialize_element(element, include_children=False))
                client._backend().perform_action(client._reference(element), "AXPress")
                return ActionResult(True, {"source": "accessibility", "locator": element.locator,
                                           "before": before, "pressed": True, "effect_verified": None})
            if target["source"] == "dom":
                selector = json.dumps(target["selector"])
                expression = (
                    f"(()=>{{const e=document.querySelector({selector});"
                    "if(!e)throw Error('Target changed');e.click();return true})()"
                )
                manager = context.services.browser
                manager.configure(context.settings)
                manager.evaluate(expression)
                return ActionResult(True, {
                    "source": "dom", "selector": target["selector"], "pressed": True, "effect_verified": None,
                })
            bounds = target["bounds"]
            report = PermissionManager().check(("accessibility",))
            if not report.granted:
                raise PermissionError(report.error)
            x, y = round(bounds["x"] + bounds["width"] / 2), round(bounds["y"] + bounds["height"] / 2)
            mouse = context.services.input.mouse
            mouse.move_mouse(x, y)
            mouse.click_mouse()
            return ActionResult(True, {
                "source": "ocr", "text": target["text"], "x": x, "y": y,
                "pressed": True, "effect_verified": None,
            })
        except Exception as exc:
            return self.failure(exc)


class SetTargetValue(AccessibilityAction):
    name = "set_target_value"
    description = "Find an editable UI target, set its value and verify the value read back"
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {**TARGET_SCHEMA, "value": {"type": "string", "required": True}}
    required_permissions = ()

    def execute(self, context, parameters):
        try:
            client = self.client(context)
            target = resolve(context, parameters, client, _find_unique)
            if target["source"] == "accessibility":
                element = target["match"].element
                if element.role not in {"AXTextField", "AXTextArea", "AXSearchField", "AXComboBox"}:
                    raise ValueError(f"Target is not an editable text field: {element.role}")
                if element.subrole == "AXSecureTextField":
                    raise ValueError("Secure text fields require a separate secret input action")
                after = client.set_value(element.id, parameters["value"])
                verified = str(after.value) == parameters["value"]
                data = {"source": "accessibility", "locator": element.locator,
                        "value": after.value, "verified": verified}
            elif target["source"] == "dom":
                selector, value = json.dumps(target["selector"]), json.dumps(parameters["value"])
                expression = f"""(()=>{{const e=document.querySelector({selector});
if(!e||!('value' in e)||e.type==='password')throw Error('Target is not an editable non-secret field');
const d=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(e),'value');
if(d&&d.set)d.set.call(e,{value});else e.value={value};
e.dispatchEvent(new Event('input',{{bubbles:true}}));e.dispatchEvent(new Event('change',{{bubbles:true}}));
return e.value=== {value};}})()"""
                manager = context.services.browser
                manager.configure(context.settings)
                observed = manager.evaluate(expression)
                verified = observed is True or observed == "true"
                data = {"source": "dom", "selector": target["selector"], "verified": verified}
            else:
                raise ValueError("OCR targets cannot be safely edited; use Accessibility or DOM")
            return ActionResult(verified, data, None if verified else "Value read back does not match",
                                None if verified else "VERIFICATION_FAILED")
        except Exception as exc:
            return self.failure(exc)


class GetUISnapshot(AccessibilityAction):
    name = "get_ui_snapshot"
    description = "Get a digest of the current app or window accessibility tree for later comparison"
    parameters_schema = {
        "application": {"type": "string", "required": False},
        "window": {"type": "string", "required": False},
    }

    def execute(self, context, parameters):
        try:
            return ActionResult(True, _snapshot(self.client(context), **(parameters or {})))
        except Exception as exc:
            return self.failure(exc)


class WaitForUIChange(AccessibilityAction):
    name = "wait_for_ui_change"
    description = "Wait until the accessibility tree differs from a supplied snapshot digest"
    parameters_schema = {
        **GetUISnapshot.parameters_schema,
        "baseline_digest": {"type": "string", "required": True},
        "timeout": {"type": "float", "required": False, "default": 10, "minimum": 0.1, "maximum": 60},
    }

    def __init__(self):
        self._cancelled = threading.Event()

    def cancel(self):
        self._cancelled.set()

    def execute(self, context, parameters):
        try:
            deadline = time.monotonic() + parameters.get("timeout", 10)
            while True:
                if self._cancelled.is_set():
                    return ActionResult(False, error="Wait was cancelled", error_code="ACTION_CANCELLED")
                current = _snapshot(self.client(context), parameters.get("application"), parameters.get("window"))
                if current["digest"] != parameters["baseline_digest"]:
                    return ActionResult(True, {**current, "changed": True})
                if time.monotonic() >= deadline:
                    return ActionResult(False, {**current, "changed": False}, "UI did not change", "TIMEOUT")
                self._cancelled.wait(0.2)
        except Exception as exc:
            return self.failure(exc)


class VerifyActionEffect(AccessibilityAction):
    name = "verify_action_effect"
    description = "Verify an accessible target's value or state after an action, optionally against its prior state"
    parameters_schema = {
        "element": {"type": "string", "required": True},
        "expected_value": {"type": "string", "required": False},
        "expected_enabled": {"type": "boolean", "required": False},
        "expected_selected": {"type": "boolean", "required": False},
        "prior_value": {"type": "string", "required": False},
    }

    def execute(self, context, parameters):
        try:
            element = self.client(context).refresh(parameters["element"])
            checks = {
                "value": "expected_value", "enabled": "expected_enabled", "selected": "expected_selected"
            }
            if not any(key in parameters for key in (*checks.values(), "prior_value")):
                raise ValueError("Provide an expected state or prior_value")
            failures = {}
            for field, key in checks.items():
                if key in parameters and getattr(element, field) != parameters[key]:
                    failures[field] = {"expected": parameters[key], "actual": getattr(element, field)}
            if "secure" in f"{element.role} {element.subrole}".casefold():
                raise ValueError("Secure field values cannot be verified through this action")
            if "prior_value" in parameters and str(element.value) == parameters["prior_value"]:
                failures["value_change"] = "Value has not changed"
            verified = not failures
            return ActionResult(verified, {
                "verified": verified, "failures": failures,
                "element": serialize_element(element, include_children=False),
            }, error=None if verified else "Observed state does not match",
                error_code=None if verified else "VERIFICATION_FAILED")
        except Exception as exc:
            return self.failure(exc)
