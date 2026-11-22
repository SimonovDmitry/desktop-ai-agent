"""Action wrappers for portable platform operations."""
from __future__ import annotations

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.privacy.confirmation import redact
from deskagent.platform.common import productivity as portable
from deskagent.platform.common.productivity import (  # noqa: F401
    MAX_ITEMS,
    SESSION,
    NAME,
    limited,
    plan_order,
    load_plan,
    status_counts,
    timestamp,
)


class ProductivityAction(Action):
    discoverable = False
    category = ActionCategory.PRODUCTIVITY

    @staticmethod
    def run(operation):
        try:
            return ActionResult(True, redact(operation()))
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="PRODUCTIVITY_ERROR")


def store_path(context):
    service = getattr(getattr(context, "services", None), "productivity", None)
    return (service or portable.ProductivityService()).store_path(context)


def with_store(context, operation):
    service = getattr(getattr(context, "services", None), "productivity", None)
    return (service or portable.ProductivityService()).with_store(context, operation)


def with_session(context, session_id, operation):
    service = getattr(getattr(context, "services", None), "productivity", None)
    return (service or portable.ProductivityService()).with_session(context, session_id, operation)


def rows(context, session_id, query, params=()):
    service = getattr(getattr(context, "services", None), "productivity", None)
    return (service or portable.ProductivityService()).rows(context, session_id, query, params)


def query_rows(context, query, params=()):
    service = getattr(getattr(context, "services", None), "productivity", None)
    return (service or portable.ProductivityService()).query_rows(context, query, params)
