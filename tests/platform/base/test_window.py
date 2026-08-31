import inspect
import pytest

from deskagent.platform.base.window import (
    WindowInformation, WindowFocus, WindowPosition, WindowSize,
    WindowState, WindowAppearance, WindowHierarchy, WindowDisplay,
    WindowArrangement, WindowGroups, WindowLifecycle,
)

WINDOW_INTERFACES = (
    WindowInformation, WindowFocus, WindowPosition, WindowSize,
    WindowState, WindowAppearance, WindowHierarchy, WindowDisplay,
    WindowArrangement, WindowGroups, WindowLifecycle,
)


def test_window_platform_interfaces_are_abstract():
    for cls in WINDOW_INTERFACES:
        assert inspect.isabstract(cls)


def test_window_interfaces_cannot_be_instantiated():
    for cls in WINDOW_INTERFACES:
        with pytest.raises(TypeError):
            cls()


@pytest.mark.parametrize(
    "interface,expected",
    [
        (WindowInformation, {
            "get_windows", "get_window", "find_windows", "get_active_window",
            "get_window_title", "get_window_position", "get_window_size",
            "get_window_bounds", "get_window_state", "get_window_application",
            "get_window_pid", "is_window_visible",
        }),
        (WindowFocus, {
            "activate", "focus", "bring_to_front", "send_to_back",
            "maximize", "unmaximize", "toggle_maximize",
        }),
        (WindowPosition, {
            "move", "move_to", "center", "center_on_display",
            "move_to_display", "snap_left", "snap_right", "snap_top",
            "snap_bottom", "restore_position",
        }),
        (WindowSize, {
            "resize", "resize_to", "set_width", "set_height", "set_size",
            "fit_to_display", "maximize_to_display", "restore_size",
        }),
        (WindowState, {
            "get_state", "set_state", "minimize", "maximize", "restore",
            "hide", "show", "toggle_visibility", "toggle_state",
        }),
        (WindowAppearance, {
            "set_always_on_top", "remove_always_on_top", "get_always_on_top",
            "set_opacity", "get_opacity", "set_fullscreen",
            "exit_fullscreen", "toggle_fullscreen",
        }),
        (WindowHierarchy, {
            "get_parent", "get_children", "get_owner",
            "get_app_windows", "get_hierarchy",
        }),
        (WindowDisplay, {
            "get_window_display", "move_to_display", "move_to_next",
            "move_to_previous", "center_on_display", "maximize_on_display",
        }),
        (WindowArrangement, {
            "arrange", "tile", "cascade", "stack", "arrange_app",
            "grid", "equalize",
        }),
        (WindowGroups, {
            "group", "ungroup", "get_group", "get_all_groups",
            "activate", "arrange",
        }),
        (WindowLifecycle, {
            "close", "close_multiple", "close_app_windows",
            "wait_for_window", "wait_for_close",
            "wait_for_visibility", "wait_for_active",
        }),
    ],
)
def test_window_interface_declares_expected_methods(interface, expected):
    assert expected <= set(dir(interface))


def test_all_declared_public_methods_are_abstract():
    for cls in WINDOW_INTERFACES:
        for name, member in inspect.getmembers(cls, inspect.isfunction):
            if not name.startswith("_"):
                assert getattr(member, "__isabstractmethod__", False), (
                    f"{cls.__name__}.{name} must be abstract"
                )
