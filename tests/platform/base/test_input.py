import inspect

import pytest

from deskagent.platform.base.input import (
    InputAutomation,
    InputClipboard,
    InputGestures,
    InputHotkeys,
    InputKeyboard,
    InputMouse,
    InputSelection,
    InputShortcuts,
    InputState,
)


INTERFACES = (
    InputKeyboard,
    InputMouse,
    InputShortcuts,
    InputHotkeys,
    InputClipboard,
    InputSelection,
    InputState,
    InputGestures,
    InputAutomation,
)

EXPECTED_METHODS = {
    InputKeyboard: {
        "press_key", "release_key", "tap_key", "hold_key", "release_all_keys",
        "press_keys", "type_text", "type_text_slowly", "paste_text", "copy_selection",
        "cut_selection", "select_all", "delete_selection", "get_keyboard_state",
    },
    InputMouse: {
        "get_mouse_position", "move_mouse", "move_mouse_relative", "click_mouse",
        "double_click_mouse", "triple_click_mouse", "mouse_down", "mouse_up",
        "drag_mouse", "drag_mouse_relative", "scroll_mouse", "horizontal_scroll_mouse",
        "move_mouse_smoothly", "get_mouse_button_state",
    },
    InputShortcuts: {
        "press_shortcut", "release_shortcut", "execute_shortcut_sequence", "copy",
        "paste", "cut", "undo", "redo", "save", "save_as", "find", "close", "quit",
        "switch_application",
    },
    InputHotkeys: {
        "register_hotkey", "unregister_hotkey", "unregister_all_hotkeys",
        "get_registered_hotkeys", "is_hotkey_registered", "trigger_hotkey",
    },
    InputClipboard: {
        "copy_text", "paste_text", "get_selected_text", "replace_selected_text",
        "append_to_clipboard", "clear_clipboard",
    },
    InputSelection: {
        "select_all_text", "select_text", "select_word", "select_line",
        "select_to_start", "select_to_end", "extend_selection", "clear_selection",
    },
    InputState: {
        "get_keyboard_state", "get_pressed_keys", "is_key_pressed",
        "get_mouse_button_state", "is_mouse_button_pressed", "get_input_state",
        "release_all_input",
    },
    InputGestures: {
        "drag_gesture", "swipe_gesture", "click_and_hold", "move_and_click",
        "move_and_double_click", "scroll_gesture", "multi_click_gesture",
    },
    InputAutomation: {
        "execute_input_sequence", "execute_input_sequence_with_delay", "wait_for_input",
        "wait_for_key", "wait_for_mouse_click", "repeat_input_action",
        "cancel_input_automation",
    },
}


def test_all_input_interfaces_are_abstract():
    for interface in INTERFACES:
        assert inspect.isabstract(interface)
        assert interface.__abstractmethods__


def test_all_declared_input_methods_are_abstract():
    for interface, expected in EXPECTED_METHODS.items():
        assert expected <= set(dir(interface))
        for name in expected:
            member = inspect.getattr_static(interface, name)
            assert getattr(member, "__isabstractmethod__", False), (
                f"{interface.__name__}.{name} must be abstract"
            )


def test_abstract_method_sets_match_the_declared_contract():
    for interface, expected in EXPECTED_METHODS.items():
        assert interface.__abstractmethods__ == expected


def test_interfaces_cannot_be_instantiated():
    for interface in INTERFACES:
        with pytest.raises(TypeError):
            interface()


def test_method_signatures_are_explicit_and_stable():
    # Validate parameter counts/names without forcing implementation details.
    for interface, expected in EXPECTED_METHODS.items():
        for name in expected:
            signature = inspect.signature(getattr(interface, name))
            assert list(signature.parameters), f"{interface.__name__}.{name} must expose parameters"
            assert list(signature.parameters)[0] == "self"

    # Exact defaults that are part of the public interface.
    checks = {
        (InputKeyboard, "tap_key", "duration"): 0.05,
        (InputKeyboard, "type_text_slowly", "interval"): 0.05,
        (InputMouse, "click_mouse", "button"): "left",
        (InputMouse, "double_click_mouse", "button"): "left",
        (InputMouse, "triple_click_mouse", "button"): "left",
        (InputMouse, "drag_mouse", "button"): "left",
        (InputMouse, "drag_mouse", "duration"): 0.5,
        (InputMouse, "drag_mouse_relative", "button"): "left",
        (InputMouse, "drag_mouse_relative", "duration"): 0.5,
        (InputMouse, "move_mouse_smoothly", "duration"): 0.5,
        (InputShortcuts, "execute_shortcut_sequence", "delay"): 0.1,
        (InputShortcuts, "save_as", "path"): None,
        (InputClipboard, "append_to_clipboard", "separator"): "\n",
        (InputSelection, "select_to_start", "scope"): "line",
        (InputSelection, "select_to_end", "scope"): "line",
        (InputGestures, "drag_gesture", "button"): "left",
        (InputGestures, "drag_gesture", "duration"): 0.5,
        (InputGestures, "swipe_gesture", "duration"): 0.3,
        (InputGestures, "move_and_click", "button"): "left",
        (InputGestures, "move_and_double_click", "button"): "left",
        (InputGestures, "multi_click_gesture", "button"): "left",
        (InputGestures, "multi_click_gesture", "interval"): 0.1,
        (InputAutomation, "wait_for_input", "timeout"): 30,
        (InputAutomation, "wait_for_key", "timeout"): 10,
        (InputAutomation, "wait_for_mouse_click", "timeout"): 10,
    }
    for (interface, method, parameter), expected_default in checks.items():
        parameter_info = inspect.signature(getattr(interface, method)).parameters[parameter]
        assert parameter_info.default == expected_default


def _make_concrete_implementation(interface):
    """Build a minimal implementation to prove the ABC contract is complete."""
    namespace = {}
    for method in interface.__abstractmethods__:
        def implementation(self, *args, **kwargs):
            return None
        implementation.__name__ = method
        namespace[method] = implementation
    return type(f"Concrete{interface.__name__}", (interface,), namespace)


@pytest.mark.parametrize("interface", INTERFACES)
def test_a_complete_subclass_satisfies_each_interface(interface):
    concrete = _make_concrete_implementation(interface)
    assert not inspect.isabstract(concrete)
    assert concrete().__class__.__mro__[1] is interface


@pytest.mark.parametrize("interface", INTERFACES)
def test_no_interface_has_accidental_public_state(interface):
    # Interfaces are intentionally pure contracts; concrete state belongs in platform classes.
    public_data = {
        name for name, value in vars(interface).items()
        if not name.startswith("_") and not callable(value)
    }
    assert public_data == set()
