import ast
import inspect
import re
import textwrap

from deskagent.actions.base import ActionRegistry
from deskagent.actions.types import ActionCategory, RiskLevel


class ActionContractError(ValueError):
    pass


class ActionContractValidator:
    PARAMETER_TYPES = {"string", "integer", "float", "boolean", "list", "dict", "string_or_int"}
    CONFIRM_ACTIONS = {
        "delete_selection", "lock_screen", "remove_from_archive", "remove_link",
        "sleep_computer", "trash_file",
    }
    DANGEROUS = re.compile(
        r"^(delete_|empty_trash$|replace_file$|clear_file$|force_quit_|restart_computer$|"
        r"shutdown_|logout_|send_(message|mail|email)|publish_|purchase_|payment_)"
    )

    def __init__(self, context=None):
        self.context = context

    def validate_registry(self, registry: ActionRegistry):
        errors = [error for action in registry.all() for error in self.validate(action)]
        if errors:
            raise ActionContractError("Invalid action contracts:\n- " + "\n- ".join(errors))
        return registry

    def validate(self, action):
        errors, label = [], f"{action.__module__}.{action.__name__}"
        if not isinstance(action.name, str) or not action.name.strip():
            errors.append(f"{label}: name must be a non-empty string")
        if not isinstance(action.description, str) or not action.description.strip():
            errors.append(f"{label}: description must be a non-empty string")
        if not isinstance(action.category, ActionCategory):
            errors.append(f"{label}: category must be ActionCategory")
        if not isinstance(action.risk_level, RiskLevel):
            errors.append(f"{label}: risk_level must be RiskLevel")
        if not callable(getattr(action, "execute", None)):
            errors.append(f"{label}: execute() is required")
        errors.extend(self._schema_errors(action, label))
        dangerous = (action.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
                     or action.name in self.CONFIRM_ACTIONS or self.DANGEROUS.search(action.name))
        if dangerous and not action.requires_confirmation:
            errors.append(f"{label}: dangerous action must require confirmation")
        if not isinstance(action.required_permissions, tuple) or not all(isinstance(x, str) for x in action.required_permissions):
            errors.append(f"{label}: required_permissions must be tuple[str, ...]")
        if self.context:
            for path in self.service_references(action):
                if not self._has_path(self.context.services, path):
                    errors.append(f"{label}: unknown service context.services.{'.'.join(path)}")
        return errors

    def _schema_errors(self, action, label):
        schema = action.parameters_schema
        if not isinstance(schema, dict):
            return [f"{label}: parameters_schema must be a dict"]
        errors = []
        for name, parameter in schema.items():
            prefix = f"{label}: parameter {name!r}"
            if not isinstance(name, str) or not isinstance(parameter, dict):
                errors.append(f"{prefix} must be a dict")
                continue
            if parameter.get("type", "string") not in self.PARAMETER_TYPES:
                errors.append(f"{prefix} has unsupported type {parameter.get('type')!r}")
            if "required" in parameter and not isinstance(parameter["required"], bool):
                errors.append(f"{prefix}.required must be boolean")
            if "enum" in parameter and not isinstance(parameter["enum"], (list, tuple)):
                errors.append(f"{prefix}.enum must be a list")
        return errors

    @staticmethod
    def service_references(action):
        try:
            tree = ast.parse(textwrap.dedent(inspect.getsource(action.execute)))
        except (OSError, TypeError, IndentationError, SyntaxError):
            return set()
        paths = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            parts, value = [], node.func
            while isinstance(value, ast.Attribute):
                parts.append(value.attr)
                value = value.value
            if isinstance(value, ast.Name) and value.id == "context":
                chain = tuple(reversed(parts))
                if chain[:1] == ("services",):
                    paths.add(chain[1:])
        return paths

    @staticmethod
    def _has_path(value, path):
        try:
            for name in path:
                value = getattr(value, name)
            return callable(value)
        except AttributeError:
            return False
