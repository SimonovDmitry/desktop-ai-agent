from types import SimpleNamespace
from unittest.mock import Mock

from deskagent.actions.accessibility.targets import ClickTarget, FindTarget, SetTargetValue, VerifyActionEffect
from deskagent.perception.accessibility.models import UIElement, UIElementMatch


def _context(client):
    return SimpleNamespace(services=SimpleNamespace(accessibility=client, browser=None), settings=SimpleNamespace())


def test_find_target_uses_accessibility_match():
    element = UIElement(id="button", locator="ax://1/button", role="AXButton", title="Save", actions=["AXPress"])
    client = Mock()
    client.find_all.return_value = [UIElementMatch(element, 1.0, True, "title")]
    result = FindTarget().execute(_context(client), {"text": "Save", "backend": "accessibility"})
    assert result.success
    assert result.data["source"] == "accessibility"
    assert result.data["element"]["locator"] == "ax://1/button"


def test_set_target_value_fails_when_readback_differs():
    element = UIElement(id="field", locator="ax://1/field", role="AXTextField", title="Name")
    client = Mock()
    client.find_all.return_value = [UIElementMatch(element, 1.0, True, "title")]
    client.set_value.return_value = UIElement(id="field", locator="ax://1/field", role="AXTextField", value="old")
    result = SetTargetValue().execute(_context(client), {"text": "Name", "value": "new", "backend": "accessibility"})
    assert not result.success
    assert result.error_code == "VERIFICATION_FAILED"


def test_verify_action_effect_detects_unchanged_value():
    client = Mock()
    client.refresh.return_value = UIElement(id="field", role="AXTextField", value="old")
    result = VerifyActionEffect().execute(_context(client), {"element": "field", "prior_value": "old"})
    assert not result.success
    assert result.data["failures"]["value_change"]


def test_find_target_redacts_secure_ax_value():
    element = UIElement(id="secret", role="AXTextField", subrole="AXSecureTextField", value="private")
    client = Mock()
    client.find_all.return_value = [UIElementMatch(element, 1.0, True, "title")]
    result = FindTarget().execute(_context(client), {"text": "Password", "backend": "accessibility"})
    assert result.success
    assert result.data["element"]["value"] == "[REDACTED]"


def test_click_target_uses_dom_when_requested():
    manager = Mock()
    manager.evaluate.side_effect = [
        [{"selector": "body > button:nth-child(1)", "text": "save", "role": "button", "bounds": {}}],
        True,
    ]
    context = SimpleNamespace(
        services=SimpleNamespace(accessibility=Mock(), browser=manager), settings=SimpleNamespace()
    )
    result = ClickTarget().execute(context, {"text": "Save", "backend": "dom"})
    assert result.success and result.data["source"] == "dom"
    assert manager.evaluate.call_count == 2
