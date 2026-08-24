import pytest

from deskagent.actions.system.display import (
    GetDisplays,
    GetDisplayBrightness,
    GetScreenSize,
    SetDisplayBrightness
)
from tests.conftest import assert_error, assert_success


@pytest.mark.parametrize("level", [0, 100])
def test_set_display_brightness_accepts_boundaries(context, level):
    result = SetDisplayBrightness().execute(context, {"brightness_level": level})
    assert_success(result, {"brightness": level})
    context.services.system.display.set_display_brightness.assert_called_once_with(level)


def test_set_display_brightness_requires_parameter(context):
    result = SetDisplayBrightness().execute(context, {})
    assert_error(result, "MISSING_PARAM")


@pytest.mark.parametrize("level", [-1, 101])
def test_set_display_brightness_rejects_out_of_range(context, level):
    result = SetDisplayBrightness().execute(context, {"brightness_level": level})
    assert_error(result, "INVALID_INPUT")
    context.services.system.display.set_display_brightness.assert_not_called()


def test_set_display_brightness_returns_system_error(context):
    context.services.system.display.set_display_brightness.side_effect = RuntimeError("brightness failed")
    result = SetDisplayBrightness().execute(context, {"brightness_level": 50})
    assert_error(result, "SYSTEM_ERROR")


def test_get_display_brightness_success(context):
    context.services.system.display.get_display_brightness.return_value = 75
    result = GetDisplayBrightness().execute(context, {})
    assert_success(result, {"brightness": 75})


def test_get_display_brightness_returns_not_supported(context):
    context.services.system.display.get_display_brightness.return_value = None
    result = GetDisplayBrightness().execute(context, {})
    assert_error(result, "NOT_SUPPORTED")


def test_get_display_brightness_returns_system_error(context):
    context.services.system.display.get_display_brightness.side_effect = RuntimeError("unsupported")
    result = GetDisplayBrightness().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")


def test_get_displays_success(context):
    displays = [{"id": 1, "primary": True}, {"id": 2, "primary": False}]
    context.services.system.display.get_displays.return_value = displays
    result = GetDisplays().execute(context, {})
    assert_success(result, {"displays": displays, "count": 2})


def test_get_displays_returns_system_error(context):
    context.services.system.display.get_displays.side_effect = RuntimeError("display failed")
    result = GetDisplays().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")


def test_get_screen_size_uses_default_display(context):
    context.services.system.display.get_screen_size.return_value = {"width": 1920, "height": 1080}
    result = GetScreenSize().execute(context, {})
    assert_success(result, {"width": 1920, "height": 1080})
    context.services.system.display.get_screen_size.assert_called_once_with(1)


def test_get_screen_size_uses_explicit_display(context):
    context.services.system.display.get_screen_size.return_value = {"width": 2560, "height": 1440}
    result = GetScreenSize().execute(context, {"display_id": 2})
    assert_success(result, {"width": 2560, "height": 1440})
    context.services.system.display.get_screen_size.assert_called_once_with(2)


def test_set_resolution_requires_all_parameters(context):
    result = SetResolution().execute(context, {"display_id": 1, "width": 1920})
    assert_error(result, "MISSING_PARAM")
    context.services.system.display.set_resolution.assert_not_called()


def test_set_resolution_success(context):
    result = SetResolution().execute(
        context, {"display_id": 1, "width": 1920, "height": 1080}
    )
    assert_success(result, {"display_id": 1, "width": 1920, "height": 1080})
    context.services.system.display.set_resolution.assert_called_once_with(1, 1920, 1080)


def test_set_resolution_returns_system_error(context):
    context.services.system.display.set_resolution.side_effect = RuntimeError("resolution failed")
    result = SetResolution().execute(
        context, {"display_id": 1, "width": 1920, "height": 1080}
    )
    assert_error(result, "SYSTEM_ERROR")
