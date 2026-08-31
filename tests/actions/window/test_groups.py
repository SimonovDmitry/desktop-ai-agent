from deskagent.actions.window.groups import *
from ._helpers import run_success_cases, run_exception_cases, target_for

CASES = [
    (GroupWindows, "groups.group", {"window_ids": [1, 2], "group_name": "work"}, {"group": "work", "windows": [1, 2]}, None),
    (UngroupWindows, "groups.ungroup", {"window_ids": [1, 2]}, {"ungrouped": [1, 2]}, None),
    (GetWindowGroup, "groups.get_group", {"window_id": 3}, {"window_id": 3, "group": "work"}, "work"),
    (GetWindowGroups, "groups.get_all_groups", {}, {"groups": {"work": [1, 2]}}, {"work": [1, 2]}),
    (ActivateWindowGroup, "groups.activate", {"group_name": "work"}, {"group": "work", "activated": True}, None),
    (ArrangeWindowGroup, "groups.arrange", {"group_name": "work", "layout": "tile"}, {"group": "work", "layout": "tile"}, None),
]

def test_success(window_context):
    run_success_cases(window_context, CASES)

def test_service_exception(window_context):
    run_exception_cases(window_context, CASES)
