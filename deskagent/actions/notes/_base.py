"""Shared validation and result handling for Apple Notes actions."""
from __future__ import annotations

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.actions.notes.backend import NotesBackend


class NotesAction(Action):
    discoverable = False
    category = ActionCategory.NOTES

    @staticmethod
    def run(operation):
        try:
            return ActionResult(True, operation())
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="NOTES_ERROR")

    @staticmethod
    def backend():
        return NotesBackend()

    def _backend(self, context):
        service = getattr(getattr(context, "services", None), "notes", None)
        return service if service is not None else self.backend()


class NotesWriteAction(NotesAction):
    discoverable = False
    risk_level = RiskLevel.MEDIUM


def required_text(value, name, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{name} must contain 1-{limit} characters")
    return value


def optional_id(value, name="id"):
    if value is None:
        return None
    return required_text(value, name, 512)


def note_id(parameters):
    return required_text(parameters["note_id"], "note_id", 512)


def bounded_limit(parameters, maximum=200, default=50):
    limit = parameters.get("limit", default)
    if type(limit) is not int or not 1 <= limit <= maximum:
        raise ValueError(f"limit must be 1-{maximum}")
    return limit
