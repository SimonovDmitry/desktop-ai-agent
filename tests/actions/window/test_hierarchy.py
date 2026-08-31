from deskagent.actions.window.hierarchy import *
from ._helpers import run_success_cases, run_exception_cases

CASES = [
    (GetWindowParent, "hierarchy.get_parent", {"window_id": 501}, {"parent_window_id": 400}, 400),
    (GetWindowChildren, "hierarchy.get_children", {"window_id": 502}, {"children": [503, 504]}, [503, 504]),
    (GetWindowOwner, "hierarchy.get_owner", {"window_id": 503}, {"application": "Safari", "pid": 1234}, {"application": "Safari", "pid": 1234}),
    (GetApplicationWindows, "hierarchy.get_app_windows", {"application": "Safari"}, {"windows": [1, 2]}, [1, 2]),
    (GetWindowHierarchy, "hierarchy.get_hierarchy", {"window_id": 504}, {"id": 504, "children": []}, {"id": 504, "children": []}),
]

def test_success(window_context):
    run_success_cases(window_context, CASES)

def test_service_exception(window_context):
    run_exception_cases(window_context, CASES)
