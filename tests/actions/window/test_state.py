from deskagent.actions.window.state import *
from ._helpers import run_success_cases, run_exception_cases

CASES = [
    (GetWindowState, "state.get_state", {"window_id": 1001}, {"window_id": 1001, "state": "normal"}, "normal"),
    (SetWindowState, "state.set_state", {"window_id": 1002, "state": "maximized"}, {"window_id": 1002, "state": "maximized"}, None),
    (MinimizeWindow, "state.minimize", {"window_id": 1003}, {"window_id": 1003, "state": "minimized"}, None),
    (MaximizeWindow, "state.maximize", {"window_id": 1004}, {"window_id": 1004, "state": "maximized"}, None),
    (RestoreWindow, "state.restore", {"window_id": 1005}, {"window_id": 1005, "state": "normal"}, None),
    (HideWindow, "state.hide", {"window_id": 1006}, {"window_id": 1006, "hidden": True}, None),
    (ShowWindow, "state.show", {"window_id": 1007}, {"window_id": 1007, "visible": True}, None),
    (ToggleWindowVisibility, "state.toggle_visibility", {"window_id": 1008}, {"window_id": 1008, "visible": False}, False),
    (ToggleWindowState, "state.toggle_state", {"window_id": 1009}, {"window_id": 1009, "state": "maximized"}, "maximized"),
]

def test_success(window_context):
    run_success_cases(window_context, CASES)

def test_service_exception(window_context):
    run_exception_cases(window_context, CASES)
