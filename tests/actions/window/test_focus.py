import pytest
from deskagent.actions.window.focus import *
from ._helpers import run_success_cases, run_exception_cases

CASES = [
    (ActivateWindow, "focus.activate", {"window_id": 401}, {"window_id": 401, "active": True}, None),
    (FocusWindow, "focus.focus", {"window_id": 402}, {"window_id": 402, "focused": True}, None),
    (BringWindowToFront, "focus.bring_to_front", {"window_id": 403}, {"window_id": 403, "front": True}, None),
    (SendWindowToBack, "focus.send_to_back", {"window_id": 404}, {"window_id": 404, "back": True}, None),
    (MinimizeWindow, "focus.minimize", {"window_id": 405}, {"window_id": 405, "state": "minimized"}, None),
    (RestoreWindow, "focus.restore", {"window_id": 406}, {"window_id": 406, "state": "normal"}, None),
    (MaximizeWindow, "focus.maximize", {"window_id": 407}, {"window_id": 407, "state": "maximized"}, None),
    (UnmaximizeWindow, "focus.restore", {"window_id": 408}, {"window_id": 408, "state": "normal"}, None),
    (ToggleWindowMaximize, "focus.toggle_maximize", {"window_id": 409}, {"window_id": 409, "state": "maximized"}, "maximized"),
]

def test_success(window_context):
    run_success_cases(window_context, CASES)

def test_service_exception(window_context):
    run_exception_cases(window_context, CASES)
