# arrangement.py currently contains the same action implementations as appearance.py.
# These tests intentionally exercise the arrangement module itself.
from .test_appearance import CASES as APPEARANCE_CASES
from .test_appearance import test_service_exception_is_converted_to_system_error as _unused

from deskagent.actions.window import arrangement
from .conftest import assert_success, assert_system_error

CASES = [
    (arrangement.SetWindowAlwaysOnTop, "appearance.set_always_on_top", {"window_id": 201, "enabled": True}, {"window_id": 201, "always_on_top": True}, None),
    (arrangement.RemoveWindowAlwaysOnTop, "appearance.set_always_on_top", {"window_id": 202}, {"window_id": 202, "always_on_top": False}, None),
    (arrangement.GetWindowAlwaysOnTop, "appearance.is_always_on_top", {"window_id": 203}, {"window_id": 203, "always_on_top": False}, False),
    (arrangement.SetWindowOpacity, "appearance.set_opacity", {"window_id": 204, "opacity": 0.25}, {"window_id": 204, "opacity": 0.25}, None),
    (arrangement.GetWindowOpacity, "appearance.get_opacity", {"window_id": 205}, {"window_id": 205, "opacity": 0.9}, 0.9),
    (arrangement.SetWindowFullscreen, "appearance.set_fullscreen", {"window_id": 206}, {"window_id": 206, "fullscreen": True}, None),
    (arrangement.ExitWindowFullscreen, "appearance.set_fullscreen", {"window_id": 207}, {"window_id": 207, "fullscreen": False}, None),
    (arrangement.ToggleWindowFullscreen, "appearance.toggle_fullscreen", {"window_id": 208}, {"window_id": 208, "fullscreen": False}, False),
]


def _target(context, path):
    obj = context.services.window
    for part in path.split('.'):
        obj = getattr(obj, part)
    return obj


def test_all_actions_success(window_context):
    for action_cls, path, params, expected, return_value in CASES:
        target = _target(window_context, path)
        if return_value is not None:
            target.return_value = return_value
        result = action_cls().execute(window_context, params)
        assert_success(result, expected)
        target.reset_mock()


def test_all_actions_convert_service_exceptions(window_context):
    for action_cls, path, params, _, _ in CASES:
        target = _target(window_context, path)
        target.side_effect = RuntimeError("arrangement failure")
        result = action_cls().execute(window_context, params)
        assert_system_error(result, "arrangement failure")
        target.side_effect = None
        target.reset_mock()
