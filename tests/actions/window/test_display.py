from deskagent.actions.window import display

from ._helpers import run_exception_cases, run_success_cases

CASES = [
    (
        display.GetWindowDisplay,
        "display.get_window_display",
        {"window_id": 301},
        {"window_id": 301, "display_id": 1},
        1,
    ),
    (
        display.MoveWindowToDisplay,
        "display.move_to_display",
        {"window_id": 302, "display_id": 2},
        {"window_id": 302, "display_id": 2},
        None,
    ),
    (
        display.MoveWindowToNextDisplay,
        "display.move_to_next",
        {"window_id": 303},
        {"window_id": 303, "display_id": 2},
        2,
    ),
    (
        display.MoveWindowToPreviousDisplay,
        "display.move_to_previous",
        {"window_id": 304},
        {"window_id": 304, "display_id": 1},
        1,
    ),
    (
        display.CenterWindowOnDisplay,
        "display.center_on_display",
        {"window_id": 305, "display_id": 1},
        {"window_id": 305, "display_id": 1, "position": {"x": 100, "y": 100}},
        {"x": 100, "y": 100},
    ),
    (
        display.MaximizeWindowOnDisplay,
        "display.maximize_on_display",
        {"window_id": 306, "display_id": 1},
        {"window_id": 306, "display_id": 1, "bounds": {"x": 0, "y": 0, "width": 1920, "height": 1080}},
        {"x": 0, "y": 0, "width": 1920, "height": 1080},
    ),
]


def test_success(window_context):
    run_success_cases(window_context, CASES)


def test_service_exception(window_context):
    run_exception_cases(window_context, CASES)
