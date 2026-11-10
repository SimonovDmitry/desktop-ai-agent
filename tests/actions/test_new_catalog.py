from deskagent.actions.registry import create_action_registry


def test_new_actions_are_registered_in_full_catalog():
    registry = create_action_registry(include_plugins=False)
    for name in (
        "capture_screen", "capture_window", "read_screen_text", "find_target", "click_target",
        "set_target_value", "wait_for_ui_change", "verify_action_effect", "get_active_dialog",
        "choose_file_in_dialog", "get_agent_capabilities", "read_pdf_pages", "get_task_progress",
        "get_page_snapshot", "wait_for_page_change", "verify_dom_element_state",
        "list_system_voices", "speak_text", "render_speech_to_file", "play_audio_file",
    ):
        assert registry.contains(name), name
