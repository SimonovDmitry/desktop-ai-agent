import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

from deskagent.actions.accessibility.interaction import (
    PerformUIElementAction,
    PressUIElement,
)
from deskagent.actions.accessibility.query import FindUIElement, GetAccessibilityStatus
from deskagent.actions.accessibility.wait import VerifyUIElementState
from deskagent.core.config import Settings
from deskagent.core.context import ActionContext
from deskagent.perception.accessibility import Point, Size, UIElement, UIElementMatch


def make_context(client):
    return ActionContext(
        Settings(), logging.getLogger("test"), SimpleNamespace(accessibility=client)
    )


def ui_element(**overrides):
    values = {
        "id": "button-id",
        "locator": "ax://42/0?role=AXButton&title=run",
        "role": "AXButton",
        "title": "Run",
        "position": Point(10, 20),
        "size": Size(100, 30),
        "actions": ["AXPress"],
        "enabled": True,
    }
    values.update(overrides)
    return UIElement(**values)


def test_find_action_returns_match_metadata():
    client = MagicMock()
    client.find.return_value = UIElementMatch(ui_element(), 0.94, False, "title")

    result = FindUIElement().execute(
        make_context(client),
        {"application": "Demo", "role": "button", "text": "Rn", "fuzzy": True},
    )

    assert result.success is True
    assert result.data["confidence"] == 0.94
    assert result.data["element"]["locator"].startswith("ax://")


def test_press_action_uses_semantic_ax_action():
    client = MagicMock()
    client.perform.return_value = ui_element()

    result = PressUIElement().execute(make_context(client), {"element": "button-id"})

    assert result.success is True
    client.perform.assert_called_once_with("button-id", "AXPress")


def test_generic_action_rejects_unsupported_native_action():
    client = MagicMock()
    client.get.return_value = ui_element()

    result = PerformUIElementAction().execute(
        make_context(client), {"element": "button-id", "ax_action": "AXDelete"}
    )

    assert result.success is False
    assert result.error_code == "UNSUPPORTED_ACTION"


def test_verify_state_reports_mismatches_without_execution_failure():
    client = MagicMock()
    client.refresh.return_value = ui_element(enabled=False, focused=True)

    result = VerifyUIElementState().execute(
        make_context(client), {"element": "button-id", "enabled": True, "focused": True}
    )

    assert result.success is True
    assert result.data["verified"] is False
    assert result.data["mismatches"] == {"enabled": {"expected": True, "actual": False}}


def test_status_does_not_require_accessibility_to_already_be_granted():
    client = MagicMock()
    client.status.return_value = {
        "supported": True,
        "trusted": False,
        "status": "denied",
    }

    result = GetAccessibilityStatus().execute(make_context(client), {})

    assert result.success is True
    assert result.data["trusted"] is False
