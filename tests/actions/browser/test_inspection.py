import json
from types import SimpleNamespace
from unittest.mock import Mock

from deskagent.actions.browser.inspection import (
    FindPageElementByRole,
    GetPageSnapshot,
    VerifyDOMElementState,
    VerifyPageText,
    WaitForPageChange,
)


def _context(manager):
    manager.configure.return_value = manager
    return SimpleNamespace(services=SimpleNamespace(browser=manager), settings=SimpleNamespace())


def test_page_snapshot_returns_digest_without_page_text():
    manager = Mock()
    manager.evaluate.return_value = json.dumps({
        "url": "https://example.com", "title": "Example", "text": "Secret page",
    })
    result = GetPageSnapshot().execute(_context(manager), {})
    assert result.success
    assert len(result.data["text_digest"]) == 64
    assert "text" not in result.data


def test_wait_for_page_change_observes_new_title():
    manager = Mock()
    manager.evaluate.return_value = json.dumps({"url": "https://example.com", "title": "New", "text": "body"})
    result = WaitForPageChange().execute(_context(manager), {"baseline": {"title": "Old"}})
    assert result.success
    assert result.data["changed"] == ["title"]


def test_dom_state_assertion_reports_mismatch():
    manager = Mock()
    manager.evaluate.return_value = json.dumps({"exists": True, "visible": False, "enabled": True})
    result = VerifyDOMElementState().execute(_context(manager), {"selector": "#save", "expected_visible": True})
    assert not result.success
    assert result.error_code == "VERIFICATION_FAILED"


def test_page_text_absence_uses_boolean_observation():
    manager = Mock()
    manager.evaluate.return_value = False
    result = VerifyPageText().execute(_context(manager), {"text": "missing", "absent": True})
    assert result.success
    assert result.data["found"] is False
    assert "includes" in manager.evaluate.call_args.args[0]


def test_find_page_element_by_role_requires_unique_match():
    manager = Mock()
    manager.evaluate.return_value = json.dumps([
        {"selector": "body > button:nth-child(1)", "role": "button", "name": "save", "bounds": {}}
    ])
    result = FindPageElementByRole().execute(_context(manager), {"role": "button", "name": "Save"})
    assert result.success
    assert result.data["element"]["selector"]
