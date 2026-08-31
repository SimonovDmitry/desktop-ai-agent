import inspect
import platform
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="macOS-only window tests",
)

pytest.importorskip("Quartz")
pytest.importorskip("AppKit")

from deskagent.platform.base.window import (
    WindowInformation, WindowFocus, WindowPosition, WindowSize,
    WindowState, WindowAppearance, WindowHierarchy, WindowDisplay,
    WindowArrangement, WindowGroups, WindowLifecycle,
)
from deskagent.platform.macos import window as macos_window


INTERFACES = (
    WindowInformation, WindowFocus, WindowPosition, WindowSize,
    WindowState, WindowAppearance, WindowHierarchy, WindowDisplay,
    WindowArrangement, WindowGroups, WindowLifecycle,
)


def implementation_for(interface):
    found = [
        cls for _, cls in inspect.getmembers(macos_window, inspect.isclass)
        if cls is not interface
        and issubclass(cls, interface)
        and cls.__module__ == macos_window.__name__
    ]
    assert len(found) == 1, (
        f"Expected exactly one implementation of {interface.__name__}, "
        f"got {[c.__name__ for c in found]}"
    )
    return found[0]


def test_all_macos_window_services_are_concrete():
    for interface in INTERFACES:
        cls = implementation_for(interface)
        assert issubclass(cls, interface)
        assert not inspect.isabstract(cls)
        cls()


@pytest.mark.parametrize("interface", INTERFACES)
def test_all_macos_window_services_expose_interface_methods(interface):
    cls = implementation_for(interface)
    for name, member in inspect.getmembers(interface, inspect.isfunction):
        if not name.startswith("_"):
            assert callable(getattr(cls, name, None)), f"{cls.__name__}.{name}"


def test_focus_activate_raises_window_after_activating_process():
    focus = implementation_for(WindowFocus)()
    if not hasattr(focus, "_get_window_metadata") or not hasattr(focus, "_run_action"):
        pytest.skip("Current focus implementation has no metadata/action helpers")

    app = MagicMock()
    app.processIdentifier.return_value = 1234
    workspace = MagicMock()
    workspace.runningApplications.return_value = [app]

    metadata = {"pid": 1234, "title": "Test", "app_name": "TestApp"}

    with patch.object(focus, "_get_window_metadata", return_value=metadata),          patch.object(focus, "_run_action") as run_action,          patch.object(macos_window.NSWorkspace, "sharedWorkspace", return_value=workspace):
        result = focus.activate(42)

    assert result == {"window_id": 42, "active": True}
    app.activateWithOptions_.assert_called_once()
    run_action.assert_called_once_with(42, 'perform action "AXRaise"')


def test_focus_unknown_window_is_safe():
    focus = implementation_for(WindowFocus)()
    if not hasattr(focus, "_get_window_metadata"):
        pytest.skip("No metadata helper")

    with patch.object(focus, "_get_window_metadata", return_value=None):
        assert focus.activate(999999) is None


@pytest.mark.parametrize(
    ("method", "command", "state"),
    [
        ("minimize",
         'perform action "AXPress" of (first button whose subrole is "AXMinimizeButton")',
         "minimized"),
        ("maximize",
         'perform action "AXPress" of (first button whose subrole is "AXZoomButton")',
         "maximized"),
    ],
)
def test_focus_window_button_actions(method, command, state):
    focus = implementation_for(WindowFocus)()
    if not hasattr(focus, "_run_action"):
        pytest.skip("No AppleScript action helper")

    with patch.object(focus, "_run_action") as run_action:
        result = getattr(focus, method)(42)

    assert result == {"window_id": 42, "state": state}
    run_action.assert_called_once_with(42, command)


def test_focus_toggle_maximize_delegates_to_maximize():
    focus = implementation_for(WindowFocus)()
    with patch.object(focus, "maximize", return_value={"ok": True}) as maximize:
        assert focus.toggle_maximize(42) == {"ok": True}
    maximize.assert_called_once_with(42)


def test_focus_unmaximize_delegates_to_maximize():
    focus = implementation_for(WindowFocus)()
    with patch.object(focus, "maximize", return_value={"ok": True}) as maximize:
        assert focus.unmaximize(42) == {"ok": True}
    maximize.assert_called_once_with(42)


def test_focus_aliases_delegate_to_activate():
    focus = implementation_for(WindowFocus)()
    with patch.object(focus, "activate", return_value={"window_id": 42, "active": True}) as activate:
        assert focus.focus(42) == {"window_id": 42, "active": True}
        assert focus.bring_to_front(42) == {"window_id": 42, "active": True}
    assert activate.call_count == 2


def test_quartz_metadata_lookup_matches_window_number():
    info_cls = implementation_for(WindowInformation)
    info = info_cls()
    if not hasattr(info, "_get_window_metadata"):
        pytest.skip("No Quartz metadata helper")

    raw = [
        {
            "kCGWindowNumber": 10,
            "kCGWindowOwnerPID": 100,
            "kCGWindowName": "Other",
            "kCGWindowOwnerName": "OtherApp",
        },
        {
            "kCGWindowNumber": 42,
            "kCGWindowOwnerPID": 1234,
            "kCGWindowName": "Target",
            "kCGWindowOwnerName": "TargetApp",
        },
    ]

    with patch.object(macos_window.Quartz, "CGWindowListCopyWindowInfo", return_value=raw):
        assert info._get_window_metadata(42) == {
            "pid": 1234,
            "title": "Target",
            "app_name": "TargetApp",
        }


def test_quartz_metadata_lookup_returns_none_for_missing_window():
    info = implementation_for(WindowInformation)()
    if not hasattr(info, "_get_window_metadata"):
        pytest.skip("No Quartz metadata helper")

    with patch.object(macos_window.Quartz, "CGWindowListCopyWindowInfo", return_value=[]):
        assert info._get_window_metadata(999) is None


def test_window_listing_maps_core_window_fields():
    info = implementation_for(WindowInformation)()
    if not hasattr(macos_window.Quartz, "CGWindowListCopyWindowInfo"):
        pytest.skip("Quartz unavailable")

    raw = [{
        "kCGWindowNumber": 42,
        "kCGWindowOwnerPID": 1234,
        "kCGWindowOwnerName": "TestApp",
        "kCGWindowName": "Main",
        "kCGWindowLayer": 0,
        "kCGWindowBounds": {"X": 10, "Y": 20, "Width": 800, "Height": 600},
    }]

    with patch.object(macos_window.Quartz, "CGWindowListCopyWindowInfo", return_value=raw):
        windows = info.get_windows()

    assert len(windows) == 1
    window = windows[0]
    assert window["id"] == 42
    assert window["application"] == "TestApp"
    assert window["pid"] == 1234
    assert window["title"] == "Main"


def test_window_information_missing_window_returns_none():
    info = implementation_for(WindowInformation)()
    with patch.object(info, "get_windows", return_value=[]):
        result = info.get_window(999)
    assert result is None


def test_window_focus_send_to_back_handles_unknown_window():
    focus = implementation_for(WindowFocus)()
    if not hasattr(focus, "_get_window_metadata"):
        pytest.skip("No metadata helper")

    with patch.object(focus, "_get_window_metadata", return_value=None):
        assert focus.send_to_back(999) is None


def test_lifecycle_wait_for_close_detects_missing_window():
    lifecycle = implementation_for(WindowLifecycle)()
    if not hasattr(lifecycle, "get_window"):
        pytest.skip("Lifecycle implementation has no get_window helper")

    with patch.object(lifecycle, "get_window", return_value=None):
        result = lifecycle.wait_for_close(42, timeout=0.1)
    assert result is not None


def test_lifecycle_wait_for_visibility_checks_requested_state():
    lifecycle = implementation_for(WindowLifecycle)()
    if not hasattr(lifecycle, "is_window_visible"):
        pytest.skip("Lifecycle implementation has no visibility helper")

    with patch.object(lifecycle, "is_window_visible", return_value=True):
        result = lifecycle.wait_for_visibility(42, timeout=0.1, visible=True)
    assert result is not None
