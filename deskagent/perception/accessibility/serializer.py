from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

from deskagent.perception.accessibility.models import UIElement, UIElementMatch


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return {key: json_safe(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    return str(value)


def serialize_element(
    element: UIElement, include_children: bool = True
) -> dict[str, Any]:
    data = {
        "id": element.id,
        "locator": element.locator,
        "role": element.role,
        "subrole": element.subrole,
        "title": element.title,
        "value": json_safe(element.value),
        "description": element.description,
        "position": json_safe(element.position),
        "size": json_safe(element.size),
        "enabled": element.enabled,
        "focused": element.focused,
        "selected": element.selected,
        "visible": element.visible,
        "actions": list(element.actions),
        "application": element.application,
        "application_pid": element.application_pid,
        "window": element.window,
        "path": list(element.path),
        "attributes": json_safe(element.attributes),
    }
    if include_children:
        data["children"] = [serialize_element(child) for child in element.children]
    return data


def serialize_match(
    match: UIElementMatch, include_children: bool = False
) -> dict[str, Any]:
    return {
        "element": serialize_element(match.element, include_children=include_children),
        "confidence": round(match.confidence, 4),
        "exact": match.exact,
        "matched_field": match.matched_field,
    }
