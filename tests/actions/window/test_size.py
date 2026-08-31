from deskagent.actions.window.size import *
from ._helpers import run_success_cases, run_exception_cases

BOUNDS = {"x": 0, "y": 0, "width": 1920, "height": 1080}
CASES = [
    (ResizeWindow, "size.resize_relative", {"window_id": 901, "delta_width": 100, "delta_height": 50}, {"window_id": 901, "width": 900, "height": 650}, {"width": 900, "height": 650}),
    (ResizeWindowTo, "size.resize_absolute", {"window_id": 902, "width": 1200, "height": 700}, {"window_id": 902, "size": {"width": 1200, "height": 700}}, None),
    (SetWindowWidth, "size.set_width", {"window_id": 903, "width": 1000}, {"width": 1000}, None),
    (SetWindowHeight, "size.set_height", {"window_id": 904, "height": 700}, {"height": 700}, None),
    (SetWindowSize, "size.resize_absolute", {"window_id": 905, "width": 800, "height": 600}, {"width": 800, "height": 600}, None),
    (FitWindowToDisplay, "size.fit_to_display", {"window_id": 906, "display_id": 2}, {"window_id": 906, "bounds": BOUNDS}, BOUNDS),
    (MaximizeWindowToDisplay, "size.maximize_on_display", {"window_id": 907, "display_id": 2}, {"window_id": 907, "bounds": BOUNDS}, BOUNDS),
    (RestoreWindowSize, "size.restore_size", {"window_id": 908}, {"window_id": 908, "size": {"width": 640, "height": 480}}, {"width": 640, "height": 480}),
]

def test_success(window_context):
    run_success_cases(window_context, CASES)

def test_service_exception(window_context):
    run_exception_cases(window_context, CASES)
