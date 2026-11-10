"""Pure analysis actions for declarative task plans."""
from __future__ import annotations

from collections import Counter

from deskagent.actions.productivity._common import ProductivityAction, load_plan, plan_order
from deskagent.actions.registry import create_action_registry
from deskagent.autopilot.validation import PlanValidator

PLAN = {"plan": {"type": "dict", "required": True}}


def _catalog():
    return create_action_registry(include_plugins=False)


class ValidateTaskPlan(ProductivityAction):
    name = "validate_task_plan"
    description = "Validate a declarative plan, actions, arguments and dependencies"
    parameters_schema = PLAN
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            try:
                plan = load_plan(parameters["plan"])
                PlanValidator(_catalog()).validate(plan)
                return {"valid": True, "step_count": len(plan.steps), "errors": []}
            except Exception as exc:
                return {"valid": False, "step_count": len(parameters["plan"].get("steps", [])),
                        "errors": str(exc).splitlines()[:100]}
        return self.run(operation)


class GetPlanDependencyOrder(ProductivityAction):
    name = "get_plan_dependency_order"
    description = "Topologically order plan steps and identify dependency layers"
    parameters_schema = PLAN
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            plan = load_plan(parameters["plan"])
            groups = plan_order(plan)
            return {"groups": groups, "ordered_step_ids": [name for group in groups for name in group],
                    "step_count": len(plan.steps)}
        return self.run(operation)


class GetPlanParallelGroups(ProductivityAction):
    name = "get_plan_parallel_groups"
    description = "Show dependency-ready groups and shared resource collisions"
    parameters_schema = PLAN
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            plan = load_plan(parameters["plan"])
            steps = {step.id: step for step in plan.steps}
            groups = []
            for layer, ids in enumerate(plan_order(plan), 1):
                resources = Counter(resource for name in ids for resource in steps[name].resources)
                groups.append({"layer": layer, "steps": ids,
                               "shared_resources": [name for name, count in resources.items() if count > 1]})
            return {"groups": groups}
        return self.run(operation)


class GetPlanCriticalPathEstimate(ProductivityAction):
    name = "get_plan_critical_path_estimate"
    description = "Estimate the longest dependency path using step timeout values"
    parameters_schema = PLAN
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            plan = load_plan(parameters["plan"])
            steps = {step.id: step for step in plan.steps}
            longest = {}
            for group in plan_order(plan):
                for name in group:
                    step = steps[name]
                    duration = step.timeout_seconds if step.timeout_seconds is not None else 1.0
                    if duration <= 0:
                        raise ValueError("Step timeout must be positive")
                    previous = max((longest[dependency][0] for dependency in step.depends_on), default=0)
                    parent = max(step.depends_on, key=lambda item: longest[item][0]) if step.depends_on else None
                    longest[name] = (previous + duration, parent)
            last = max(longest, key=lambda item: longest[item][0])
            path, current = [], last
            while current:
                path.append(current)
                current = longest[current][1]
            return {"estimated_seconds": round(longest[last][0], 3),
                    "critical_step_ids": list(reversed(path)),
                    "method": "sum of timeouts; steps without timeout count as one second"}
        return self.run(operation)


class GetPlanRiskSummary(ProductivityAction):
    name = "get_plan_risk_summary"
    description = "Summarize action risk levels and unknown actions in a plan"
    parameters_schema = PLAN
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            plan = load_plan(parameters["plan"])
            catalog = _catalog()
            counts, unknown = Counter(), []
            for step in plan.steps:
                if catalog.contains(step.action):
                    counts[catalog.get(step.action).risk_level.value] += 1
                else:
                    unknown.append({"step_id": step.id, "action": step.action})
            return {"steps_by_risk": dict(counts), "unknown_actions": unknown}
        return self.run(operation)


class GetPlanActionUsage(ProductivityAction):
    name = "get_plan_action_usage"
    description = "Count actions and categories used by a plan"
    parameters_schema = PLAN
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            plan = load_plan(parameters["plan"])
            catalog = _catalog()
            actions = Counter(step.action for step in plan.steps)
            categories = Counter(catalog.get(step.action).category.value if catalog.contains(step.action)
                                 else "unknown" for step in plan.steps)
            return {"actions": dict(actions), "categories": dict(categories)}
        return self.run(operation)


class GetPlanRetryBudget(ProductivityAction):
    name = "get_plan_retry_budget"
    description = "Count allowed attempts and possible retries across a plan"
    parameters_schema = PLAN
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            plan = load_plan(parameters["plan"])
            attempts = [{"step_id": step.id, "max_attempts": step.retry.max_attempts,
                         "retry_strategy": step.retry.strategy}
                        for step in plan.steps]
            return {"total_max_attempts": sum(item["max_attempts"] for item in attempts),
                    "possible_retries": sum(max(0, item["max_attempts"] - 1) for item in attempts),
                    "steps": attempts}
        return self.run(operation)


class GetPlanConfirmationSteps(ProductivityAction):
    name = "get_plan_confirmation_steps"
    description = "Find steps that declare or inherit a confirmation requirement"
    parameters_schema = PLAN
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            plan = load_plan(parameters["plan"])
            catalog = _catalog()
            items = []
            for step in plan.steps:
                action = catalog.get(step.action) if catalog.contains(step.action) else None
                if step.requires_confirmation or (action and action.requires_confirmation):
                    items.append({"step_id": step.id, "action": step.action,
                                  "step_requires_confirmation": step.requires_confirmation,
                                  "action_requires_confirmation": bool(action and action.requires_confirmation)})
            return {"steps": items, "total": len(items)}
        return self.run(operation)


class GetPlanVerificationCoverage(ProductivityAction):
    name = "get_plan_verification_coverage"
    description = "Summarize declared checks for each step in a plan"
    parameters_schema = PLAN
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            plan = load_plan(parameters["plan"])
            entries = [{"step_id": step.id, "checks": [item.type.value for item in step.verifications]}
                       for step in plan.steps]
            return {"steps": entries, "without_checks": [
                item["step_id"] for item in entries if not item["checks"]
            ]}
        return self.run(operation)


class CompareTaskPlans(ProductivityAction):
    name = "compare_task_plans"
    description = "Compare step additions, removals and changed definitions between plans"
    parameters_schema = {"first_plan": {"type": "dict", "required": True},
                         "second_plan": {"type": "dict", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            first = load_plan(parameters["first_plan"])
            second = load_plan(parameters["second_plan"])
            left = {step.id: step.definition_dict() for step in first.steps}
            right = {step.id: step.definition_dict() for step in second.steps}
            return {"added": sorted(set(right) - set(left)),
                    "removed": sorted(set(left) - set(right)),
                    "changed": sorted(name for name in set(left) & set(right) if left[name] != right[name]),
                    "unchanged": sum(left[name] == right[name] for name in set(left) & set(right))}
        return self.run(operation)
