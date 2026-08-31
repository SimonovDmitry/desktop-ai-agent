from deskagent.actions.window.position import *
from ._helpers import run_success_cases, run_exception_cases

SNAP = {"pos": {"x": 0, "y": 0}, "size": {"width": 500, "height": 800}}
CASES = [
    (MoveWindow, "position.move", {"window_id": 801, "dx": 10, "dy": -20}, {"window_id": 801, "position": {"x": 110, "y": 80}}, {"x": 110, "y": 80}),
    (MoveWindowTo, "position.move_to", {"window_id": 802, "x": 50, "y": 60}, {"window_id": 802, "position": {"x": 50, "y": 60}}, None),
    (CenterWindow, "position.center", {"window_id": 803}, {"window_id": 803, "position": {"x": 300, "y": 200}}, {"x": 300, "y": 200}),
    (CenterWindowOnDisplay, "position.center_on_display", {"window_id": 804, "display_id": 2}, {"window_id": 804, "display_id": 2, "position": {"x": 400, "y": 300}}, {"x": 400, "y": 300}),
    (MoveWindowToDisplay, "position.move_to_display", {"window_id": 805, "display_id": 2}, {"window_id": 805, "display_id": 2}, None),
    (SnapWindowLeft, "position.snap", {"window_id": 806}, {"window_id": 806, "position": SNAP["pos"], "size": SNAP["size"]}, SNAP),
    (SnapWindowRight, "position.snap", {"window_id": 807}, {"window_id": 807, "position": SNAP["pos"], "size": SNAP["size"]}, SNAP),
    (SnapWindowTop, "position.snap", {"window_id": 808}, {"window_id": 808, "position": SNAP["pos"], "size": SNAP["size"]}, SNAP),
    (SnapWindowBottom, "position.snap", {"window_id": 809}, {"window_id": 809, "position": SNAP["pos"], "size": SNAP["size"]}, SNAP),
    (RestoreWindowPosition, "position.restore_position", {"window_id": 810}, {"window_id": 810, "position": {"x": 5, "y": 6}}, {"x": 5, "y": 6}),
]

def test_success(window_context):
    run_success_cases(window_context, CASES)

def test_service_exception(window_context):
    run_exception_cases(window_context, CASES)
