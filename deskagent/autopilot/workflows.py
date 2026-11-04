from __future__ import annotations

import re
import sqlite3
from datetime import UTC, datetime, timedelta
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from deskagent.autopilot.models import AutopilotMode, Plan
from deskagent.autopilot.store import SessionStore
from deskagent.autopilot.validation import PlanValidator


PLACEHOLDER = re.compile(r"\$\{(inputs|variables)\.([A-Za-z0-9_-]+)\}")


class WorkflowValidationError(ValueError):
    pass


class WorkflowRegistry:
    """Versioned, declarative YAML workflows without executable expressions."""

    def __init__(self, store: SessionStore, validator: PlanValidator):
        self.store = store
        self.validator = validator

    def save(self, definition: str | Path | dict[str, Any]) -> dict[str, Any]:
        value = self._migrate(self._load(definition))
        name = value.get("name")
        if not isinstance(name, str) or not name.strip():
            raise WorkflowValidationError("Workflow requires a non-empty name")
        version = int(value.get("version", 1))
        if version < 1:
            raise WorkflowValidationError("Workflow version must be positive")
        self._validate_inputs_schema(value.get("inputs", {}))
        self._validate_permissions(value.get("required_permissions", []))
        self.instantiate(value, self._sample_inputs(value), validate_inputs=False)
        try:
            self.store.put_workflow(name, version, value)
        except sqlite3.IntegrityError as exc:
            raise WorkflowValidationError(f"Workflow {name!r} version {version} already exists") from exc
        return value

    def update(self, name: str, definition: str | Path | dict[str, Any]) -> dict[str, Any]:
        current = self.get(name)
        value = self._load(definition)
        value["name"] = name
        value["version"] = int(current.get("version", 1)) + 1
        return self.save(value)

    def enable(self, name: str):
        self.store.set_workflow_state(name, enabled=True)

    def disable(self, name: str):
        self.store.set_workflow_state(name, enabled=False)

    def archive(self, name: str):
        self.store.set_workflow_state(name, archived=True)

    def delete(self, name: str):
        self.store.delete_workflow(name)

    def export_yaml(self, name: str, version: int | None = None) -> str:
        return yaml.safe_dump(self.get(name, version), allow_unicode=True, sort_keys=False)

    def import_yaml(self, value: str | Path) -> dict[str, Any]:
        return self.save(value)

    def get(self, name: str, version: int | None = None) -> dict[str, Any]:
        return self.store.get_workflow(name, version)

    def list(self, detailed: bool = False) -> list[dict[str, Any]]:
        rows = self.store.list_workflows()
        if detailed:
            return rows
        return [{"name": row["name"], "version": row["version"]} for row in rows]

    def instantiate(
        self, definition: dict[str, Any], inputs: dict[str, Any] | None = None, validate_inputs: bool = True
    ) -> Plan:
        inputs = self._inputs(definition, inputs or {}, require_all=validate_inputs)
        rendered_inputs = {
            name: (f"${{secrets.{value}}}" if definition.get("inputs", {}).get(name, {}).get("secret") else value)
            for name, value in inputs.items()
        }
        variables = self._render(deepcopy(definition.get("variables", {})), rendered_inputs, {})
        variables = self._render(variables, rendered_inputs, variables)
        raw_steps = self._render(deepcopy(definition.get("steps", [])), rendered_inputs, variables)
        plan = Plan.from_dict(
            {
                "version": 1,
                "metadata": {
                    "workflow": definition.get("name"),
                    "workflow_version": int(definition.get("version", 1)),
                    "inputs": {
                        name: (
                            "***SECRET_REF***"
                            if definition.get("inputs", {}).get(name, {}).get("secret")
                            else value
                        )
                        for name, value in inputs.items()
                    },
                    "required_permissions": definition.get("required_permissions", []),
                },
                "steps": raw_steps,
            }
        )
        return self.validator.validate(plan)

    def run(self, engine, name: str, inputs: dict[str, Any] | None = None,
            mode: AutopilotMode = AutopilotMode.GUIDED, dry_run: bool = False):
        definition = self.get(name)
        plan = self.instantiate(definition, inputs)
        title = definition.get("title") or name
        session = engine.create_session(f"Run workflow: {title}", plan, mode, dry_run=dry_run)
        self.store.start_workflow_run(name, int(definition.get("version", 1)), session.id, inputs or {})
        return engine.start(session.id)

    def due(self, now: datetime | None = None) -> list[dict[str, Any]]:
        now = now or datetime.now(UTC)
        due = []
        for item in self.list(detailed=True):
            definition = self.get(item["name"])
            schedule = definition.get("schedule") or {}
            next_run = schedule.get("next_run_at")
            if next_run and datetime.fromisoformat(next_run) <= now:
                due.append(definition)
        return due

    def advance_schedule(self, name: str, from_time: datetime | None = None):
        definition = self.get(name)
        schedule = definition.get("schedule") or {}
        interval = float(schedule.get("interval_seconds", 0))
        if interval <= 0:
            raise WorkflowValidationError("Schedule requires a positive interval_seconds")
        base = from_time or datetime.now(UTC)
        schedule["next_run_at"] = (base + timedelta(seconds=interval)).isoformat()
        definition["schedule"] = schedule
        return self.update(name, definition)

    def _inputs(self, definition, provided, require_all=True):
        result = self._default_inputs(definition, require_all=False)
        unknown = set(provided) - set(definition.get("inputs", {}))
        if unknown:
            raise WorkflowValidationError(f"Unknown inputs: {', '.join(sorted(unknown))}")
        result.update(provided)
        for name, schema in definition.get("inputs", {}).items():
            if name not in result:
                if require_all and schema.get("required", False):
                    raise WorkflowValidationError(f"Missing required input: {name}")
                continue
            self._validate_value(name, result[name], schema)
        return result

    @staticmethod
    def _default_inputs(definition, require_all=False):
        result = {}
        for name, schema in definition.get("inputs", {}).items():
            if "default" in schema:
                result[name] = schema["default"]
            elif require_all and schema.get("required"):
                raise WorkflowValidationError(f"Missing required input: {name}")
        return result

    @staticmethod
    def _sample_inputs(definition):
        samples = {
            "string": "sample", "integer": 0, "float": 0.0,
            "boolean": False, "list": [], "dict": {},
        }
        result = {}
        for name, schema in definition.get("inputs", {}).items():
            if "default" in schema:
                result[name] = schema["default"]
            elif "enum" in schema and schema["enum"]:
                result[name] = schema["enum"][0]
            elif "minimum" in schema:
                result[name] = schema["minimum"]
            else:
                result[name] = samples[schema.get("type", "string")]
        return result

    @staticmethod
    def _validate_inputs_schema(inputs):
        if not isinstance(inputs, dict):
            raise WorkflowValidationError("inputs must be an object")
        for name, schema in inputs.items():
            if not isinstance(schema, dict):
                raise WorkflowValidationError(f"Input {name} schema must be an object")
            if schema.get("type", "string") not in {
                "string", "integer", "float", "boolean", "list", "dict",
            }:
                raise WorkflowValidationError(f"Input {name} has unsupported type")
            if "secret" in schema and not isinstance(schema["secret"], bool):
                raise WorkflowValidationError(f"Input {name}.secret must be boolean")

    @staticmethod
    def _validate_value(name, value, schema):
        expected = {
            "string": str,
            "integer": int,
            "float": (int, float),
            "boolean": bool,
            "list": list,
            "dict": dict,
        }[schema.get("type", "string")]
        if isinstance(value, bool) != (expected is bool) or not isinstance(value, expected):
            raise WorkflowValidationError(f"Input {name} has invalid type")
        if "minimum" in schema and value < schema["minimum"]:
            raise WorkflowValidationError(f"Input {name} is below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise WorkflowValidationError(f"Input {name} is above maximum")
        if "enum" in schema and value not in schema["enum"]:
            raise WorkflowValidationError(f"Input {name} is not an allowed value")

    def _render(self, value: Any, inputs: dict[str, Any], variables: dict[str, Any]) -> Any:
        if isinstance(value, dict):
            return {key: self._render(item, inputs, variables) for key, item in value.items()}
        if isinstance(value, list):
            return [self._render(item, inputs, variables) for item in value]
        if not isinstance(value, str):
            return value
        matches = list(PLACEHOLDER.finditer(value))
        if len(matches) == 1 and matches[0].span() == (0, len(value)):
            scope, name = matches[0].groups()
            source = inputs if scope == "inputs" else variables
            if name not in source:
                raise WorkflowValidationError(f"Unknown {scope} value: {name}")
            return source[name]

        def replace(match):
            scope, name = match.groups()
            source = inputs if scope == "inputs" else variables
            if name not in source:
                raise WorkflowValidationError(f"Unknown {scope} value: {name}")
            return str(source[name])

        return PLACEHOLDER.sub(replace, value)

    @staticmethod
    def _load(definition):
        if isinstance(definition, dict):
            return deepcopy(definition)
        text = Path(definition).read_text(encoding="utf-8") if isinstance(definition, Path) else definition
        value = yaml.safe_load(text)
        if not isinstance(value, dict):
            raise WorkflowValidationError("Workflow must be a YAML object")
        return value

    @staticmethod
    def _validate_permissions(permissions):
        if not isinstance(permissions, list) or not all(isinstance(item, str) for item in permissions):
            raise WorkflowValidationError("required_permissions must be a list of strings")

    @staticmethod
    def _migrate(value):
        result = deepcopy(value)
        version = int(result.get("schema_version", 1))
        if version > 2:
            raise WorkflowValidationError(f"Unsupported workflow schema version: {version}")
        if version == 1:
            for step in result.get("steps", []):
                if "tool" in step and "action" not in step:
                    step["action"] = step.pop("tool")
            result["schema_version"] = 2
        return result
