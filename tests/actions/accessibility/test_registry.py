from deskagent.actions.contracts import ActionContractValidator
from deskagent.actions.registry import discover_actions


EXPECTED_ACTIONS = {
    "get_accessibility_status",
    "request_accessibility_permission",
    "get_focused_ui_element",
    "get_application_ui_tree",
    "get_window_ui_tree",
    "list_ui_elements",
    "get_ui_element",
    "find_ui_element",
    "find_ui_elements_by_text",
    "find_ui_elements_by_role",
    "get_ui_element_actions",
    "get_ui_element_bounds",
    "get_ui_element_value",
    "press_ui_element",
    "focus_ui_element",
    "set_ui_element_value",
    "select_ui_element",
    "expand_ui_element",
    "collapse_ui_element",
    "increment_ui_element",
    "decrement_ui_element",
    "scroll_ui_element",
    "show_ui_element_menu",
    "perform_ui_element_action",
    "wait_for_ui_element",
    "wait_for_ui_element_disappear",
    "wait_for_ui_element_enabled",
    "wait_for_ui_value",
    "verify_ui_element_state",
}


def test_all_accessibility_actions_are_discoverable_and_valid():
    actions = discover_actions(
        packages=("deskagent.actions.accessibility",), include_plugins=False
    )
    names = {action.name for action in actions}

    assert EXPECTED_ACTIONS <= names
    assert not [
        error
        for action in actions
        for error in ActionContractValidator().validate(action)
    ]
