import pytest

from deskagent.actions.system.mouse import (
    Click,
    DoubleClick,
    DragMouse,
    GetCursorPosition,
    MoveMouse,
    ScrollMouse,
)
from tests.conftest import assert_error, assert_success


def test_get_cursor_position_success(context):
    context.services.system.mouse.get_cursor_position.return_value = {"x": 10, "y": 20}
    result = GetCursorPosition().execute(context, {})
    assert_success(result, {"x": 10, "y": 20})


def test_get_cursor_position_system_error(context):
    context.services.system.mouse.get_cursor_position.side_effect = RuntimeError("mouse failed")
    result = GetCursorPosition().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")


def test_move_mouse_requires_coordinates(context):
    result = MoveMouse().execute(context, {"x": 10})
    assert_error(result, "MISSING_PARAM")
    context.services.system.mouse.move_mouse.assert_not_called()


def test_move_mouse_success(context):
    result = MoveMouse().execute(context, {"x": 10, "y": 20})
    assert_success(result, {"x": 10, "y": 20})
    context.services.system.mouse.move_mouse.assert_called_once_with(10, 20)


def test_move_mouse_system_error(context):
    context.services.system.mouse.move_mouse.side_effect = RuntimeError("move failed")
    result = MoveMouse().execute(context, {"x": 10, "y": 20})
    assert_error(result, "SYSTEM_ERROR")


@pytest.mark.parametrize("action_class,method", [(Click, "click"), (DoubleClick, "double_click")])
def test_click_actions_use_default_button(context, action_class, method):
    result = action_class().execute(context, {})
    assert_success(result, {"button": "left"})
    getattr(context.services.system.mouse, method).assert_called_once_with("left")


@pytest.mark.parametrize("action_class,method", [(Click, "click"), (DoubleClick, "double_click")])
def test_click_actions_accept_supported_buttons(context, action_class, method):
    result = action_class().execute(context, {"button": "right"})
    assert_success(result, {"button": "right"})
    getattr(context.services.system.mouse, method).assert_called_once_with("right")


@pytest.mark.parametrize("action_class", [Click, DoubleClick])
def test_click_actions_reject_unknown_button(context, action_class):
    result = action_class().execute(context, {"button": "invalid"})
    assert_error(result, "INVALID_BUTTON")


@pytest.mark.parametrize("action_class,method", [(Click, "click"), (DoubleClick, "double_click")])
def test_click_actions_system_error(context, action_class, method):
    getattr(context.services.system.mouse, method).side_effect = RuntimeError("click failed")
    result = action_class().execute(context, {"button": "left"})
    assert_error(result, "SYSTEM_ERROR")


def test_drag_mouse_requires_all_coordinates(context):
    result = DragMouse().execute(context, {"x1": 0, "y1": 0, "x2": 10})
    assert_error(result, "MISSING_PARAM")


def test_drag_mouse_success(context):
    result = DragMouse().execute(
        context, {"x1": 0, "y1": 0, "x2": 100, "y2": 200}
    )
    assert_success(result, {"from": (0, 0), "to": (100, 200)})
    context.services.system.mouse.drag_mouse.assert_called_once_with(0, 0, 100, 200)


def test_drag_mouse_system_error(context):
    context.services.system.mouse.drag_mouse.side_effect = RuntimeError("drag failed")
    result = DragMouse().execute(
        context, {"x1": 0, "y1": 0, "x2": 100, "y2": 200}
    )
    assert_error(result, "SYSTEM_ERROR")


def test_scroll_mouse_requires_clicks(context):
    result = ScrollMouse().execute(context, {})
    assert_error(result, "MISSING_PARAM")


def test_scroll_mouse_accepts_positive_and_negative_values(context):
    for clicks in (5, -5, 0):
        result = ScrollMouse().execute(context, {"clicks": clicks})
        assert_success(result, {"clicks": clicks})
    assert context.services.system.mouse.scroll_mouse.call_count == 3


def test_scroll_mouse_system_error(context):
    context.services.system.mouse.scroll_mouse.side_effect = RuntimeError("scroll failed")
    result = ScrollMouse().execute(context, {"clicks": 1})
    assert_error(result, "SYSTEM_ERROR")
