import platform
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-only tests")

from deskagent.platform.macos.system import (
    MacOSSystemAudio,
    MacOSSystemClipboard,
    MacOSSystemDisplay,
    MacOSSystemInformation,
    MacOSSystemMouse,
    MacOSSystemNetwork,
    MacOSSystemNotification,
    MacOSSystemPower,
)


def test_audio_set_volume_calls_osascript():
    with patch("deskagent.platform.macos.system.run") as run:
        MacOSSystemAudio().set_volume(50)
        run.assert_called_once_with(["osascript", "-e", "set volume output volume 50"])


@pytest.mark.parametrize("value", [None, "50"])
def test_audio_set_volume_validates_input(value):
    with pytest.raises(ValueError):
        MacOSSystemAudio().set_volume(value)


def test_audio_mute_calls_osascript():
    with patch("deskagent.platform.macos.system.run") as run:
        MacOSSystemAudio().mute()
        run.assert_called_once_with(["osascript", "-e", "set volume output muted true"])


def test_audio_unmute_calls_osascript():
    with patch("deskagent.platform.macos.system.run") as run:
        MacOSSystemAudio().unmute()
        run.assert_called_once_with(["osascript", "-e", "set volume output muted false"])


def test_audio_increase_volume_reads_current_value_and_sets_new_value():
    with patch("deskagent.platform.macos.system.check_output", return_value=b"40\\n") as check_output, \
         patch("deskagent.platform.macos.system.run") as run:
        MacOSSystemAudio().increase_volume(10)

    check_output.assert_called_once()
    run.assert_called_once_with(["osascript", "-e", "set volume output volume 50"])


def test_audio_decrease_volume_uses_default_step():
    with patch("deskagent.platform.macos.system.check_output", return_value=b"40\\n"), \
         patch("deskagent.platform.macos.system.run") as run:
        MacOSSystemAudio().decrease_volume()

    run.assert_called_once_with(["osascript", "-e", "set volume output volume 30"])


def test_audio_get_volume_returns_platform_value():
    with patch("deskagent.platform.macos.system.check_output", return_value=b"42\\n"):
        assert MacOSSystemAudio().get_volume() == "42"


def test_clipboard_get_text():
    pasteboard = MagicMock()
    pasteboard.stringForType_.return_value = "hello"
    with patch("deskagent.platform.macos.system.NSPasteboard.generalPasteboard", return_value=pasteboard):
        assert MacOSSystemClipboard().get_clipboard() == "hello"


def test_clipboard_set_text():
    pasteboard = MagicMock()
    with patch("deskagent.platform.macos.system.NSPasteboard.generalPasteboard", return_value=pasteboard):
        MacOSSystemClipboard().set_clipboard("hello")
    pasteboard.clearContents.assert_called_once_with()
    pasteboard.setString_forType_.assert_called_once()


def test_display_brightness_clamps_to_range():
    with patch("deskagent.platform.macos.system.run") as run:
        MacOSSystemDisplay().set_display_brightness(120)
    run.assert_called_once()
    script = run.call_args.args[0][2]
    assert "repeat 16 times" in script


def test_display_get_brightness_is_currently_unimplemented():
    assert MacOSSystemDisplay().get_display_brightness() is None


def test_information_unimplemented_methods_are_explicitly_pending():
    info = MacOSSystemInformation()
    assert info.system_info() is None
    assert info.get_cpu_info() is None
    assert info.get_disk_info() is None
    assert info.get_os_info() is None
    assert info.get_user_info() is None


def test_mouse_unimplemented_methods_are_explicitly_pending():
    mouse = MacOSSystemMouse()
    assert mouse.move_mouse() is None
    assert mouse.click() is None
    assert mouse.double_click() is None
    assert mouse.drag_mouse() is None
    assert mouse.scroll_mouse() is None


def test_network_hostname_is_real_shape():
    with patch("deskagent.platform.macos.system.socket.gethostname", return_value="host"), \
         patch("deskagent.platform.macos.system.socket.getfqdn", return_value="host.local"):
        assert MacOSSystemNetwork().get_hostname() == {
            "hostname": "host",
            "fqdn": "host.local",
        }


def test_notification_delegates_to_osascript():
    with patch("deskagent.platform.macos.system.run") as run:
        MacOSSystemNotification().send_notification("Title", "Hello", None)
    run.assert_called_once()


def test_power_service_exposes_required_methods():
    power = MacOSSystemPower()
    for name in (
        "lock_screen",
        "sleep_computer",
        "restart_computer",
        "shutdown_computer",
        "logout_computer",
        "cancel_shutdown_computer",
    ):
        assert callable(getattr(power, name))
