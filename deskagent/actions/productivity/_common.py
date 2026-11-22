"""Bounded read-only helpers for persisted tasks and workflow plans."""
from __future__ import annotations

import sqlite3
from collections import Counter, deque
from datetime import datetime
from pathlib import Path

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.autopilot.models import Plan
from deskagent.autopilot.store import SessionStore
from deskagent.privacy.confirmation import redact

MAX_ITEMS = 500
SESSION = {"session_id": {"type": "string", "required": True}}
NAME = {"name": {"type": "string", "required": True}}


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
    path = Path(context.settings.storage.autopilot).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Autopilot session store does not exist: {path}")
    return path


def with_store(context, operation):
    store = SessionStore(store_path(context))
    try:
        return operation(store)
    finally:
        store.close()


def with_session(context, session_id, operation):
    return with_store(context, lambda store: operation(store, store.get(session_id)))


def rows(context, session_id, query, params=()):
    with sqlite3.connect(f"{store_path(context).as_uri()}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        exists = connection.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not exists:
            raise KeyError(session_id)
        return [dict(row) for row in connection.execute(query, (session_id, *params)).fetchmany(MAX_ITEMS + 1)]


def query_rows(context, query, params=()):
    with sqlite3.connect(f"{store_path(context).as_uri()}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(query, params).fetchmany(MAX_ITEMS + 1)]


def limited(items, limit=100):
    items = list(items)
    return {"items": items[:limit], "total": len(items), "truncated": len(items) > limit}


def plan_order(plan):
    steps = {step.id: step for step in plan.steps}
    if len(steps) != len(plan.steps):
        raise ValueError("Plan contains duplicate step ids")
    outgoing = {key: [] for key in steps}
    indegree = {key: 0 for key in steps}
    for step in plan.steps:
        for dependency in step.depends_on:
            if dependency not in steps:
                raise ValueError(f"Unknown dependency: {dependency}")
            outgoing[dependency].append(step.id)
            indegree[step.id] += 1
    ready = deque(step.id for step in plan.steps if indegree[step.id] == 0)
    groups, visited = [], 0
    while ready:
        group = list(ready)
        ready.clear()
        groups.append(group)
        visited += len(group)
        for step_id in group:
            for successor in outgoing[step_id]:
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    ready.append(successor)
    if visited != len(steps):
        raise ValueError("Plan contains a dependency cycle")
    return groups


def load_plan(value):
    if not isinstance(value, dict):
        raise ValueError("Plan must be an object")
    plan = Plan.from_dict(value)
    if not 1 <= len(plan.steps) <= 100:
        raise ValueError("Plan must have 1-100 steps")
    plan_order(plan)
    return plan


def status_counts(steps):
    return dict(Counter(step.status.value for step in steps))


def timestamp(value):
    return datetime.fromisoformat(value) if value else None
