from deskagent.actions.window.lifecycle import *
from ._helpers import run_success_cases, run_exception_cases

CASES = [
    (CloseWindow, "lifecycle.close", {"window_id": 701}, {"closed": True, "window_id": 701}, None),
    (CloseWindows, "lifecycle.close_multiple", {"window_ids": [701, 702]}, {"closed": [701, 702]}, {"closed": [701, 702]}),
    (CloseApplicationWindows, "lifecycle.close_app_windows", {"application": "Safari"}, {"application": "Safari", "closed_count": 3}, 3),
    (WaitForWindow, "lifecycle.wait_for_window", {"title": "Ready", "timeout": 5}, {"found": True, "window": {"id": 703}}, {"id": 703}),
    (WaitForWindowClose, "lifecycle.wait_for_close", {"window_id": 704, "timeout": 6}, {"closed": True}, None),
    (WaitForWindowVisible, "lifecycle.wait_for_visibility", {"window_id": 705, "timeout": 7}, {"visible": True}, None),
    (WaitForWindowActive, "lifecycle.wait_for_active", {"window_id": 706, "timeout": 8}, {"active": True}, None),
]

def test_success(window_context):
    run_success_cases(window_context, CASES)

def test_service_exception_is_timeout(window_context):
    run_exception_cases(window_context, CASES, error_code="TIMEOUT", message="timed out")
