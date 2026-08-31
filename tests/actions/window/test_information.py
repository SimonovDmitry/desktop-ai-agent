from deskagent.actions.window.information import *
from ._helpers import run_success_cases, run_exception_cases, target_for

CASES = [
    (GetWindows, "information.get_windows", {"application": "Safari", "visible_only": False}, {"windows": [1, 2], "count": 2}, [1, 2]),
    (GetWindow, "information.get_window_info", {"window_id": 601}, {"id": 601, "title": "Test"}, {"id": 601, "title": "Test"}),
    (FindWindows, "information.find_windows", {"title": "Test", "title_contains": "Tes", "application": "Safari"}, {"windows": [1], "count": 1}, [1]),
    (GetActiveWindow, "information.get_active_window", {}, {"id": 602}, {"id": 602}),
    (GetWindowBounds, "information.get_window_bounds", {"window_id": 603}, {"x": 10, "y": 20, "width": 800, "height": 600}, {"x": 10, "y": 20, "width": 800, "height": 600}),
    (GetWindowState, "information.get_window_state", {"window_id": 604}, {"state": "maximized"}, "maximized"),
    (GetWindowApplication, "information.get_window_application", {"window_id": 605}, {"application": "Safari", "pid": 999}, {"application": "Safari", "pid": 999}),
    (IsWindowVisible, "information.is_window_visible", {"window_id": 606}, {"visible": True}, True),
]

def test_success(window_context):
    run_success_cases(window_context, CASES)

def test_get_windows_defaults(window_context):
    target = target_for(window_context, "information.get_windows")
    target.return_value = []
    result = GetWindows().execute(window_context, {})
    assert result.success is True
    assert result.data == {"windows": [], "count": 0}
    target.assert_called_once_with(application=None, visible_only=True)

def test_get_windows_accepts_none_parameters(window_context):
    target = target_for(window_context, "information.get_windows")
    target.return_value = [1]
    result = GetWindows().execute(window_context, None)
    assert result.success is True
    assert result.data == {"windows": [1], "count": 1}
    target.assert_called_once_with(application=None, visible_only=True)

def test_get_window_returns_not_found_for_falsy_info(window_context):
    target = target_for(window_context, "information.get_window_info")
    target.return_value = None
    result = GetWindow().execute(window_context, {"window_id": 607})
    assert result.success is False
    assert result.error == "Window with ID 607 not found"
    assert result.error_code == "NOT_FOUND"

def test_service_exception(window_context):
    run_exception_cases(window_context, CASES)
