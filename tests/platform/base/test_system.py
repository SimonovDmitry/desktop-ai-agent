import inspect

from deskagent.platform.base.system import (
    SystemAudio,
    SystemClipboard,
    SystemDisplay,
    SystemInformation,
    SystemMouse,
    SystemNetwork,
    SystemNotification,
    SystemPower,
)


def test_platform_interfaces_are_abstract():
    for cls in (
        SystemAudio,
        SystemClipboard,
        SystemDisplay,
        SystemInformation,
        SystemMouse,
        SystemNetwork,
        SystemNotification,
        SystemPower,
    ):
        assert inspect.isabstract(cls)


def test_audio_interface_declares_expected_methods():
    assert {"set_volume", "increase_volume", "mute", "decrease_volume", "unmute", "get_volume"} <= set(
        dir(SystemAudio)
    )


def test_clipboard_interface_declares_expected_methods():
    assert {"get_clipboard", "set_clipboard", "clean_clipboard"} <= set(dir(SystemClipboard))


def test_display_interface_declares_expected_methods():
    assert {"set_display_brightness", "get_display_brightness", "get_displays", "get_screen_size", "set_resolution"} <= set(
        dir(SystemDisplay)
    )


def test_information_interface_declares_expected_methods():
    expected = {
        "get_cpu_processes", "get_memory_processes", "get_disk_processes",
        "get_battery_status", "get_uptime", "get_current_time", "get_current_date",
        "system_info", "get_cpu_info", "get_disk_info", "get_os_info", "get_user_info",
    }
    assert expected <= set(dir(SystemInformation))


def test_mouse_interface_declares_expected_methods():
    expected = {"get_cursor_position", "move_mouse", "click", "double_click", "drag_mouse", "scroll_mouse"}
    assert expected <= set(dir(SystemMouse))


def test_network_interface_declares_expected_methods():
    expected = {
        "get_network_status", "get_ip_address", "get_hostname",
        "get_network_interfaces", "get_public_ip_address", "get_default_gateway",
        "get_dns", "ping_host", "check_internet_connection",
    }
    assert expected <= set(dir(SystemNetwork))


def test_notification_interface_declares_expected_methods():
    assert {"send_notification", "clear_agent_notification"} <= set(dir(SystemNotification))


def test_power_interface_declares_expected_methods():
    expected = {
        "lock_screen", "sleep_computer", "restart_computer",
        "shutdown_computer", "logout_computer", "cancel_shutdown_computer",
    }
    assert expected <= set(dir(SystemPower))
