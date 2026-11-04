from __future__ import annotations


class SessionPresenter:
    """Framework-neutral view model for desktop, CLI or API session screens."""

    @staticmethod
    def present(session, events=None):
        completed = sum(step.status.value in {"succeeded", "skipped"} for step in session.plan.steps)
        total = len(session.plan.steps)
        return {
            "id": session.id,
            "goal": session.goal,
            "status": session.status.value,
            "mode": session.mode.value,
            "progress": {"completed": completed, "total": total,
                         "percent": round(completed / total * 100, 1) if total else 0},
            "current_step_id": session.current_step_id,
            "pending_confirmation": session.pending_confirmation,
            "error": session.error,
            "plan_version": session.plan.version,
            "steps": [
                {
                    "id": step.id,
                    "title": step.title,
                    "action": step.action,
                    "status": step.status.value,
                    "attempts": step.attempts,
                    "depends_on": list(step.depends_on),
                    "retry_at": step.retry_at,
                    "error": step.error,
                    "error_code": step.error_code,
                    "output": step.output,
                }
                for step in session.plan.steps
            ],
            "events": list(events or []),
            "available_actions": SessionPresenter._available_actions(session),
        }

    @staticmethod
    def _available_actions(session):
        status = session.status.value
        return {
            "start": status == "ready",
            "pause": status == "running",
            "resume": status == "paused",
            "cancel": status not in {"completed", "cancelled"},
            "approve": status == "waiting_for_user",
        }
