from __future__ import annotations

from deskagent.actions.base import ActionRegistry
from deskagent.autopilot.models import Plan


class PlanValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid plan:\n- " + "\n- ".join(errors))


class PlanValidator:
    def __init__(self, registry: ActionRegistry | None = None, max_steps: int = 100):
        self.registry = registry
        self.max_steps = max_steps

    def validate(self, plan: Plan) -> Plan:
        errors: list[str] = []
        if not plan.steps:
            errors.append("plan must contain at least one step")
        if len(plan.steps) > self.max_steps:
            errors.append(f"plan exceeds the {self.max_steps} step limit")

        ids = [step.id for step in plan.steps]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            errors.append(f"duplicate step ids: {', '.join(duplicates)}")

        known = set(ids)
        for step in plan.steps:
            if not step.id or not step.title or not step.action:
                errors.append("every step requires id, title and action")
            missing = sorted(set(step.depends_on) - known)
            if missing:
                errors.append(f"step {step.id!r} has unknown dependencies: {', '.join(missing)}")
            if step.id in step.depends_on:
                errors.append(f"step {step.id!r} depends on itself")
            if self.registry and not self.registry.contains(step.action):
                errors.append(f"step {step.id!r} uses unknown action {step.action!r}")
            elif self.registry:
                errors.extend(self._argument_errors(step.id, self.registry.get(step.action).parameters_schema,
                                                    step.arguments))
            if step.retry.max_attempts < 1:
                errors.append(f"step {step.id!r} max_attempts must be positive")
            if step.timeout_seconds is not None and step.timeout_seconds <= 0:
                errors.append(f"step {step.id!r} timeout must be positive")
            if step.retry.jitter_seconds < 0:
                errors.append(f"step {step.id!r} retry jitter cannot be negative")
            if step.retry.strategy not in {"fixed", "linear", "exponential"}:
                errors.append(f"step {step.id!r} has unsupported retry strategy")
            if step.compensation and self.registry:
                if not self.registry.contains(step.compensation.action):
                    errors.append(
                        f"step {step.id!r} uses unknown compensation action "
                        f"{step.compensation.action!r}"
                    )
                else:
                    errors.extend(self._argument_errors(
                        f"{step.id}.compensation",
                        self.registry.get(step.compensation.action).parameters_schema,
                        step.compensation.arguments,
                    ))
            for verification in step.verifications:
                if verification.timeout_seconds < 0 or verification.interval_seconds < 0:
                    errors.append(f"step {step.id!r} verification timing cannot be negative")

        errors.extend(self._cycle_errors(plan))
        if errors:
            raise PlanValidationError(errors)
        return plan

    @staticmethod
    def _cycle_errors(plan: Plan) -> list[str]:
        graph = {step.id: step.depends_on for step in plan.steps}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            if any(dependency in graph and visit(dependency) for dependency in graph.get(node, ())):
                return True
            visiting.remove(node)
            visited.add(node)
            return False

        return ["plan contains a dependency cycle"] if any(visit(node) for node in graph) else []

    @staticmethod
    def _argument_errors(step_id, schema, arguments):
        errors = []
        unknown = set(arguments) - set(schema)
        if unknown:
            errors.append(f"step {step_id!r} has unknown arguments: {', '.join(sorted(unknown))}")
        for name, parameter in schema.items():
            if parameter.get("required") and name not in arguments:
                errors.append(f"step {step_id!r} is missing required argument {name!r}")
            if name not in arguments or (
                isinstance(arguments[name], str) and arguments[name].startswith("${")
            ):
                continue
            expected = {
                "string": str,
                "integer": int,
                "float": (int, float),
                "boolean": bool,
                "list": list,
                "dict": dict,
                "string_or_int": (str, int),
            }.get(parameter.get("type", "string"))
            value = arguments[name]
            if expected and (isinstance(value, bool) != (expected is bool) or not isinstance(value, expected)):
                errors.append(f"step {step_id!r} argument {name!r} has invalid type")
        return errors
