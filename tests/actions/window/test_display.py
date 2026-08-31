# display.py currently contains the same implementations as appearance.py.
from deskagent.actions.window import display
from ._helpers import run_success_cases, run_exception_cases

CASES = [
    (display.SetWindowAlwaysOnTop, "appearance.set_always_on_top", {"window_id": 301, "enabled": True}, {"window_id": 301, "always_on_top": True}, None),
    (display.RemoveWindowAlwaysOnTop, "appearance.set_always_on_top", {"window_id": 302}, {"window_id": 302, "always_on_top": False}, None),
    (display.GetWindowAlwaysOnTop, "appearance.is_always_on_top", {"window_id": 303}, {"window_id": 303, "always_on_top": False}, False),
    (display.SetWindowOpacity, "appearance.set_opacity", {"window_id": 304, "opacity": 0.25}, {"window_id": 304, "opacity": 0.25}, None),
    (display.GetWindowOpacity, "appearance.get_opacity", {"window_id": 305}, {"window_id": 305, "opacity": 0.9}, 0.9),
    (display.SetWindowFullscreen, "appearance.set_fullscreen", {"window_id": 306}, {"window_id": 306, "fullscreen": True}, None),
    (display.ExitWindowFullscreen, "appearance.set_fullscreen", {"window_id": 307}, {"window_id": 307, "fullscreen": False}, None),
    (display.ToggleWindowFullscreen, "appearance.toggle_fullscreen", {"window_id": 308}, {"window_id": 308, "fullscreen": False}, False),
]

def test_success(window_context):
    run_success_cases(window_context, CASES)

def test_service_exception(window_context):
    run_exception_cases(window_context, CASES)
