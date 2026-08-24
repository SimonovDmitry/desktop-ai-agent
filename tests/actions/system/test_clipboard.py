from deskagent.actions.system.clipboard import (
    CleanClipboard,
    GetClipboard,
    SetClipboard,
)
from tests.conftest import assert_error, assert_success


def test_get_clipboard_returns_text(context):
    context.services.system.clipboard.get_clipboard.return_value = "hello"
    result = GetClipboard().execute(context, {})
    assert_success(result, {"content": "hello"})
    context.services.system.clipboard.get_clipboard.assert_called_once_with()


def test_get_clipboard_empty_clipboard(context):
    context.services.system.clipboard.get_clipboard.return_value = None
    result = GetClipboard().execute(context, {})
    assert_success(result, {"content": ""})


def test_get_clipboard_returns_system_error(context):
    context.services.system.clipboard.get_clipboard.side_effect = RuntimeError("clipboard failed")
    result = GetClipboard().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")


def test_set_clipboard_requires_text(context):
    result = SetClipboard().execute(context, {})
    assert_error(result, "MISSING_PARAM")
    context.services.system.clipboard.set_clipboard.assert_not_called()


def test_set_clipboard_success(context):
    result = SetClipboard().execute(context, {"text": "hello"})
    assert_success(result, {"text_length": 5})
    context.services.system.clipboard.set_clipboard.assert_called_once_with("hello")


def test_set_clipboard_allows_empty_text(context):
    result = SetClipboard().execute(context, {"text": ""})
    assert_success(result, {"text_length": 0})
    context.services.system.clipboard.set_clipboard.assert_called_once_with("")


def test_set_clipboard_returns_system_error(context):
    context.services.system.clipboard.set_clipboard.side_effect = RuntimeError("set failed")
    result = SetClipboard().execute(context, {"text": "hello"})
    assert_error(result, "SYSTEM_ERROR")


def test_clean_clipboard_success(context):
    result = CleanClipboard().execute(context, {})
    assert_success(result, {"cleared": True})
    context.services.system.clipboard.clean_clipboard.assert_called_once_with()


def test_clean_clipboard_returns_system_error(context):
    context.services.system.clipboard.clean_clipboard.side_effect = RuntimeError("clean failed")
    result = CleanClipboard().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")
