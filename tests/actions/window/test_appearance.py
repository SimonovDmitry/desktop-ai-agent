import pytest

from deskagent.actions.window.appearance import (
    ExitWindowFullscreen,
    GetWindowAlwaysOnTop,
    GetWindowOpacity,
    RemoveWindowAlwaysOnTop,
    SetWindowAlwaysOnTop,
    SetWindowFullscreen,
    SetWindowOpacity,
    ToggleWindowFullscreen,
)
from ._helpers import run_success_cases, run_exception_cases, target_for

CASES = [
    (SetWindowAlwaysOnTop, "appearance.set_always_on_top", {"window_id": 101, "enabled": True}, {"window_id": 101, "always_on_top": True}, None),
    (RemoveWindowAlwaysOnTop, "appearance.set_always_on_top", {"window_id": 102}, {"window_id": 102, "always_on_top": False}, None),
    (GetWindowAlwaysOnTop, "appearance.is_always_on_top", {"window_id": 103}, {"window_id": 103, "always_on_top": True}, True),
    (SetWindowOpacity, "appearance.set_opacity", {"window_id": 104, "opacity": 0.75}, {"window_id": 104, "opacity": 0.75}, None),
    (GetWindowOpacity, "appearance.get_opacity", {"window_id": 105}, {"window_id": 105, "opacity": 0.55}, 0.55),
    (SetWindowFullscreen, "appearance.set_fullscreen", {"window_id": 106}, {"window_id": 106, "fullscreen": True}, None),
    (ExitWindowFullscreen, "appearance.set_fullscreen", {"window_id": 107}, {"window_id": 107, "fullscreen": False}, None),
    (ToggleWindowFullscreen, "appearance.toggle_fullscreen", {"window_id": 108}, {"window_id": 108, "fullscreen": True}, True),
]


def test_success(window_context):
    run_success_cases(window_context, CASES)


def test_service_exception(window_context):
    run_exception_cases(window_context, CASES)


def test_set_and_remove_always_on_top_pass_exact_arguments(window_context):
    target = target_for(window_context, "appearance.set_always_on_top")
    SetWindowAlwaysOnTop().execute(window_context, {"window_id": 10, "enabled": True})
    target.assert_called_once_with(10, True)
    target.reset_mock()
    RemoveWindowAlwaysOnTop().execute(window_context, {"window_id": 10})
    target.assert_called_once_with(10, False)


def test_fullscreen_actions_pass_exact_arguments(window_context):
    target = target_for(window_context, "appearance.set_fullscreen")
    SetWindowFullscreen().execute(window_context, {"window_id": 11})
    target.assert_called_once_with(11, True)
    target.reset_mock()
    ExitWindowFullscreen().execute(window_context, {"window_id": 11})
    target.assert_called_once_with(11, False)
