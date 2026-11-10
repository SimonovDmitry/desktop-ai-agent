from __future__ import annotations

from pathlib import Path

from deskagent.actions.base import Action
from deskagent.actions.registry import discover_actions
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.autopilot.store import SessionStore
from deskagent.privacy.confirmation import redact
from deskagent.ui.autopilot import SessionPresenter


SESSION_SCHEMA = {"session_id": {"type": "string", "required": True}}


def _session(context, session_id):
    path = Path(context.settings.storage.autopilot).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Autopilot session store does not exist: {path}")
    store = SessionStore(path)
    try:
        return store.get(session_id)
    finally:
        store.close()


class GetTaskProgress(Action):
    name = "get_task_progress"
    description = "Read persisted task status, steps, progress and pending confirmation"
    category = ActionCategory.PRODUCTIVITY
    parameters_schema = SESSION_SCHEMA

    def execute(self, context, parameters):
        try:
            return ActionResult(True, redact(SessionPresenter.present(_session(context, parameters["session_id"]))))
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="SESSION_ERROR")


class PreviewTaskEffects(Action):
    name = "preview_task_effects"
    description = "Preview actions, arguments and declared risks in a persisted task plan without executing it"
    category = ActionCategory.PRODUCTIVITY
    parameters_schema = SESSION_SCHEMA

    def execute(self, context, parameters):
        try:
            session = _session(context, parameters["session_id"])
            catalog = {action.name: action for action in discover_actions(include_plugins=False)}
            effects = []
            for step in session.plan.steps:
                action = catalog.get(step.action)
                effects.append(redact({
                    "step_id": step.id, "title": step.title, "action": step.action,
                    "arguments": step.arguments, "risk": action.risk_level.value if action else "unknown",
                    "category": action.category.value if action else "unknown",
                    "requires_confirmation": action.requires_confirmation if action else True,
                }))
            return ActionResult(True, {
                "session_id": session.id, "plan_version": session.plan.version, "effects": effects,
            })
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="SESSION_ERROR")


class ExplainLastActionFailure(Action):
    name = "explain_last_action_failure"
    description = "Read the most recent failed step and give a concise recovery suggestion"
    category = ActionCategory.PRODUCTIVITY
    parameters_schema = SESSION_SCHEMA

    GUIDANCE = {
        "PERMISSION_DENIED": "Grant the requested macOS permission, then retry the step.",
        "ELEMENT_NOT_FOUND": "Inspect the current UI tree and refine the target locator.",
        "TIMEOUT": "Check whether the target app is responsive, then retry.",
        "VERIFICATION_FAILED": "Inspect the observed state before retrying the action.",
        "ACTION_CANCELLED": "Review the pending approval and resume the task if appropriate.",
    }

    def execute(self, context, parameters):
        try:
            session = _session(context, parameters["session_id"])
            failed = next((step for step in reversed(session.plan.steps) if step.error), None)
            if failed is None:
                return ActionResult(True, {"session_id": session.id, "failure": None})
            return ActionResult(True, redact({
                "session_id": session.id, "step_id": failed.id, "action": failed.action,
                "error": failed.error, "error_code": failed.error_code,
                "suggestion": self.GUIDANCE.get(failed.error_code, "Inspect the action result and current app state."),
            }))
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="SESSION_ERROR")
