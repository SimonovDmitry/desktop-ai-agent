import platform
import plistlib
import subprocess
from unittest.mock import MagicMock, call, patch

import pytest

pytestmark = pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-only tests")

from deskagent.platform.macos.application import (
    MacOSApplicationDocuments,
    MacOSApplicationFocus,
    MacOSApplicationInformation,
    MacOSApplicationInstances,
    MacOSApplicationLifecycle,
    MacOSApplicationPreferences,
    MacOSApplicationProcesses,
    MacOSApplicationResources,
    MacOSApplicationStartup,
)


def app(name="Safari", pid=123, bundle="com.apple.Safari", hidden=False, arch=0x0100000C):
    obj = MagicMock()
    obj.localizedName.return_value = name
    obj.processIdentifier.return_value = pid
    obj.bundleIdentifier.return_value = bundle
    obj.isHidden.return_value = hidden
    obj.activationPolicy.return_value = 0
    obj.executableArchitecture.return_value = arch
    return obj


# Lifecycle

def test_lifecycle_launch_without_arguments():
    service = MacOSApplicationLifecycle()
    with patch.object(service, "_get_pid_by_name", return_value=123), \
         patch("deskagent.platform.macos.application.subprocess.run") as run, \
         patch("deskagent.platform.macos.application.time.sleep") as sleep:
        result = service.launch("Safari")
    run.assert_called_once_with(["open", "-a", "Safari"], check=True)
    sleep.assert_called_once_with(0.5)
    assert result == {"application": "Safari", "pid": 123, "launched": True}


def test_lifecycle_launch_with_arguments():
    service = MacOSApplicationLifecycle()
    with patch.object(service, "_get_pid_by_name", return_value=123), \
         patch("deskagent.platform.macos.application.subprocess.run") as run, \
         patch("deskagent.platform.macos.application.time.sleep"):
        service.launch("Chrome", ["--new-window", "https://example.com"])
    run.assert_called_once_with(
        ["open", "-a", "Chrome", "--args", "--new-window", "https://example.com"], check=True
    )


def test_lifecycle_launch_hidden():
    service = MacOSApplicationLifecycle()
    with patch.object(service, "_get_pid_by_name", return_value=456), \
         patch("deskagent.platform.macos.application.subprocess.run") as run, \
         patch("deskagent.platform.macos.application.time.sleep"):
        result = service.launch_hidden("Terminal")
    run.assert_called_once_with(["open", "-g", "-a", "Terminal"], check=True)
    assert result == {"application": "Terminal", "pid": 456, "launched": True, "hidden": True}


def test_lifecycle_quit():
    with patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert MacOSApplicationLifecycle().quit("Safari") == {"application": "Safari", "quit": True}
    run.assert_called_once_with(["osascript", "-e", 'quit app "Safari"'], check=True)


@pytest.mark.parametrize("identifier", [12345, "12345"])
def test_lifecycle_force_quit_pid(identifier):
    with patch("deskagent.platform.macos.application.subprocess.run") as run:
        result = MacOSApplicationLifecycle().force_quit(identifier)
    run.assert_called_once_with(["kill", "-9", "12345"], check=True)
    assert result == {"application": identifier, "terminated": True}


def test_lifecycle_force_quit_name():
    with patch("deskagent.platform.macos.application.subprocess.run") as run:
        result = MacOSApplicationLifecycle().force_quit("Safari")
    run.assert_called_once_with(["killall", "Safari"], check=True)
    assert result == {"application": "Safari", "terminated": True}


def test_lifecycle_restart_composes_quit_wait_launch():
    service = MacOSApplicationLifecycle()
    with patch.object(service, "quit") as quit_, patch.object(service, "wait_for_exit") as wait_, \
         patch.object(service, "launch", return_value={"application": "Safari", "pid": 7, "launched": True}) as launch_:
        result = service.restart("Safari")
    quit_.assert_called_once_with("Safari")
    wait_.assert_called_once_with("Safari", timeout=10)
    launch_.assert_called_once_with("Safari")
    assert result == {"application": "Safari", "pid": 7, "launched": True}


def test_lifecycle_wait_for_start_success_without_sleep():
    service = MacOSApplicationLifecycle()
    with patch.object(service, "_get_pid_by_name", return_value=77), \
         patch("deskagent.platform.macos.application.time.time", side_effect=[10.0, 10.25]), \
         patch("deskagent.platform.macos.application.time.sleep") as sleep:
        result = service.wait_for_start("Photoshop")
    assert result == {"application": "Photoshop", "started": True, "pid": 77, "waited": 0.25}
    sleep.assert_not_called()


def test_lifecycle_wait_for_start_timeout():
    service = MacOSApplicationLifecycle()
    with patch.object(service, "_get_pid_by_name", return_value=None), \
         patch("deskagent.platform.macos.application.time.time", side_effect=[0.0, 30.1]), \
         patch("deskagent.platform.macos.application.time.sleep"):
        with pytest.raises(TimeoutError, match="Photoshop.*30s"):
            service.wait_for_start("Photoshop", timeout=30)


def test_lifecycle_wait_for_exit_success_without_sleep():
    service = MacOSApplicationLifecycle()
    with patch.object(service, "_get_pid_by_name", return_value=None), \
         patch("deskagent.platform.macos.application.time.time", side_effect=[10.0, 10.2]), \
         patch("deskagent.platform.macos.application.time.sleep") as sleep:
        result = service.wait_for_exit("Safari")
    assert result == {"application": "Safari", "exited": True, "waited": 0.2}
    sleep.assert_not_called()


def test_lifecycle_wait_for_exit_timeout():
    service = MacOSApplicationLifecycle()
    with patch.object(service, "_get_pid_by_name", return_value=123), \
         patch("deskagent.platform.macos.application.time.time", side_effect=[0.0, 30.1]), \
         patch("deskagent.platform.macos.application.time.sleep"):
        with pytest.raises(TimeoutError, match="Safari.*30s"):
            service.wait_for_exit("Safari", timeout=30)


def test_lifecycle_launch_or_activate_existing_app():
    target = app(pid=555)
    workspace = MagicMock()
    workspace.runningApplications.return_value = [target]
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        result = MacOSApplicationLifecycle().launch_or_activate("sAfArI")
    target.activateWithOptions_.assert_called_once()
    assert result == {"application": "sAfArI", "action": "activated", "pid": 555}


def test_lifecycle_launch_or_activate_starts_missing_app():
    service = MacOSApplicationLifecycle()
    workspace = MagicMock()
    workspace.runningApplications.return_value = []
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace), \
         patch.object(service, "launch", return_value={"application": "Safari", "pid": 888, "launched": True}) as launch_:
        result = service.launch_or_activate("Safari")
    launch_.assert_called_once_with("Safari")
    assert result == {"application": "Safari", "action": "launched", "pid": 888}


# Information

def test_information_get_running_filters_activation_policy():
    regular = app("Safari", 1)
    helper = app("Helper", 2)
    helper.activationPolicy.return_value = 1
    workspace = MagicMock()
    workspace.runningApplications.return_value = [regular, helper]
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        assert MacOSApplicationInformation().get_running() == [{"name": "Safari", "pid": 1, "bundle_id": "com.apple.Safari"}]


def test_information_get_installed_parses_mdfind():
    with patch("deskagent.platform.macos.application.subprocess.check_output", return_value="/Applications/Safari.app\n/Applications/Chrome.app\n"):
        assert MacOSApplicationInformation().get_installed() == [
            {"name": "Safari", "path": "/Applications/Safari.app"},
            {"name": "Chrome", "path": "/Applications/Chrome.app"},
        ]


def test_information_get_installed_returns_empty_on_error():
    with patch("deskagent.platform.macos.application.subprocess.check_output", side_effect=OSError):
        assert MacOSApplicationInformation().get_installed() == []


def test_information_find_is_case_insensitive_and_limited():
    service = MacOSApplicationInformation()
    installed = [
        {"name": "Chrome", "path": "/Chrome.app"},
        {"name": "Chrome Canary", "path": "/Canary.app"},
        {"name": "Chromium", "path": "/Chromium.app"},
    ]
    with patch.object(service, "get_installed", return_value=installed):
        assert service.find("CHROME", limit=2) == installed[:2]


def test_information_get_info_aggregates_metadata(tmp_path):
    root = tmp_path / "Safari.app"
    plist = root / "Contents" / "Info.plist"
    plist.parent.mkdir(parents=True)
    with plist.open("wb") as fh:
        plistlib.dump({
            "CFBundleIdentifier": "com.apple.Safari",
            "CFBundleShortVersionString": "18.5",
        }, fh)
    service = MacOSApplicationInformation()
    with patch.object(service, "get_path", return_value=str(root)), \
         patch.object(service, "_get_running_app_by_name", return_value=app(pid=321)):
        assert service.get_info("Safari") == {
            "name": "Safari", "pid": 321, "path": str(root),
            "bundle_id": "com.apple.Safari", "version": "18.5", "architecture": "arm64",
        }


def test_information_get_info_raises_when_missing():
    service = MacOSApplicationInformation()
    with patch.object(service, "get_path", return_value=None):
        with pytest.raises(ValueError, match="Safari.*not found"):
            service.get_info("Safari")


def test_information_get_status_running_visible_active():
    target = app(pid=100)
    workspace = MagicMock()
    workspace.frontmostApplication.return_value = target
    service = MacOSApplicationInformation()
    with patch.object(service, "_get_running_app_by_name", return_value=target), \
         patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        assert service.get_status("Safari") == {"running": True, "visible": True, "active": True, "pid": 100}


def test_information_get_status_missing():
    service = MacOSApplicationInformation()
    with patch.object(service, "_get_running_app_by_name", return_value=None):
        assert service.get_status("Safari") == {"running": False, "visible": False, "active": False, "pid": None}


def test_information_is_running_and_get_pid():
    service = MacOSApplicationInformation()
    target = app(pid=99)
    with patch.object(service, "_get_running_app_by_name", return_value=target):
        assert service.is_running("Safari") is True
        assert service.get_pid("Safari") == 99
    with patch.object(service, "_get_running_app_by_name", return_value=None):
        assert service.is_running("Safari") is False
        assert service.get_pid("Safari") is None


def test_information_get_active_returns_frontmost_shape():
    target = app("Safari", 42)
    workspace = MagicMock()
    workspace.frontmostApplication.return_value = target
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        assert MacOSApplicationInformation().get_active() == {"name": "Safari", "pid": 42, "bundle_id": "com.apple.Safari"}


def test_information_get_active_returns_none_without_frontmost_app():
    workspace = MagicMock()
    workspace.frontmostApplication.return_value = None
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        assert MacOSApplicationInformation().get_active() is None


def test_information_get_path_returns_first_mdfind_match():
    with patch("deskagent.platform.macos.application.subprocess.check_output", return_value="/Applications/Safari.app\n/Other/Safari.app\n"):
        assert MacOSApplicationInformation().get_path("Safari") == "/Applications/Safari.app"


def test_information_get_path_returns_none_on_error():
    with patch("deskagent.platform.macos.application.subprocess.check_output", side_effect=OSError):
        assert MacOSApplicationInformation().get_path("Safari") is None


def test_information_bundle_id_version_and_executable_path(tmp_path):
    root = tmp_path / "Safari.app"
    plist = root / "Contents" / "Info.plist"
    plist.parent.mkdir(parents=True)
    with plist.open("wb") as fh:
        plistlib.dump({"CFBundleIdentifier": "com.apple.Safari", "CFBundleShortVersionString": "18.5", "CFBundleExecutable": "Safari"}, fh)
    service = MacOSApplicationInformation()
    with patch.object(service, "get_path", return_value=str(root)):
        assert service.get_bundle_id("Safari") == "com.apple.Safari"
        assert service.get_version("Safari") == "18.5"
        assert service.get_executable_path("Safari") == str(root / "Contents/MacOS/Safari")


@pytest.mark.parametrize(("arch_code", "expected"), [(0x0100000C, "arm64"), (0x01000007, "x86_64")])
def test_information_get_architecture_for_running_app(arch_code, expected):
    service = MacOSApplicationInformation()
    with patch.object(service, "_get_running_app_by_name", return_value=app(arch=arch_code)):
        assert service.get_architecture("Safari") == expected


def test_information_get_architecture_uses_lipo_when_not_running():
    service = MacOSApplicationInformation()
    with patch.object(service, "_get_running_app_by_name", return_value=None), \
         patch.object(service, "get_executable_path", return_value="/Safari"), \
         patch("deskagent.platform.macos.application.subprocess.check_output", return_value="arm64 x86_64\n") as check:
        assert service.get_architecture("Safari") == "arm64 x86_64"
    check.assert_called_once_with(["lipo", "-archs", "/Safari"], text=True)


@pytest.mark.parametrize(("kind", "identifier", "expected"), [
    ("pid", 123, "Safari"),
    ("path", "/Applications/Safari.app", "Safari"),
])
def test_information_get_name_from_id(kind, identifier, expected):
    workspace = MagicMock()
    workspace.runningApplications.return_value = [app(pid=123)]
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        assert MacOSApplicationInformation().get_name_from_id(kind, identifier) == expected


def test_information_get_name_from_bundle_id():
    workspace = MagicMock()
    workspace.runningApplications.return_value = []
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace), \
         patch("deskagent.platform.macos.application.subprocess.check_output", return_value="/Applications/Safari.app\n"):
        assert MacOSApplicationInformation().get_name_from_id("bundle_id", "com.apple.Safari") == "Safari"


def test_information_get_name_from_id_unknown():
    workspace = MagicMock()
    workspace.runningApplications.return_value = []
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        assert MacOSApplicationInformation().get_name_from_id("pid", 999) == "Unknown"


# Preferences

def test_preferences_get_permissions_aggregates_checks():
    service = MacOSApplicationPreferences()
    with patch.object(service, "get_accessibility_status", return_value=True), \
         patch.object(service, "get_automation_status", return_value=False), \
         patch.object(service, "get_notification_status", return_value=True):
        assert service.get_permissions("DeskAgent") == {"accessibility": True, "automation": False, "notifications": True}


def test_preferences_accessibility_status_uses_ax_trust():
    with patch("deskagent.platform.macos.application.AXIsProcessTrusted", return_value=1):
        assert MacOSApplicationPreferences().get_accessibility_status("DeskAgent") is True
    with patch("deskagent.platform.macos.application.AXIsProcessTrusted", return_value=0):
        assert MacOSApplicationPreferences().get_accessibility_status("DeskAgent") is False


def test_preferences_automation_status_success_and_failure():
    with patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert MacOSApplicationPreferences().get_automation_status("Safari") is True
    run.assert_called_once_with(["osascript", "-e", 'tell application "Safari" to get name'], capture_output=True, timeout=1)
    with patch("deskagent.platform.macos.application.subprocess.run", side_effect=RuntimeError):
        assert MacOSApplicationPreferences().get_automation_status("Safari") is False


def test_preferences_notification_status_is_true():
    assert MacOSApplicationPreferences().get_notification_status("DeskAgent") is True


def test_preferences_default_app_uses_uttype():
    url = MagicMock()
    url.path.return_value = "/System/Applications/Preview.app"
    workspace = MagicMock()
    workspace.URLForApplicationToOpenContentType_.return_value = url
    with patch("deskagent.platform.macos.application.UTType.typeWithFilenameExtension_", return_value=MagicMock()) as type_ , \
         patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        assert MacOSApplicationPreferences().get_default_app(".pdf") == "Preview"
    type_.assert_called_once_with("pdf")


def test_preferences_open_with():
    service = MacOSApplicationPreferences()
    with patch("deskagent.platform.macos.application.os.path.exists", return_value=True), \
         patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert service.open_with("/tmp/file.pdf", "Preview") is True
    run.assert_called_once_with(["open", "-a", "Preview", "/tmp/file.pdf"], check=True)


def test_preferences_open_with_missing_file():
    with patch("deskagent.platform.macos.application.os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            MacOSApplicationPreferences().open_with("/tmp/missing.pdf", "Preview")


def test_preferences_open_app_prefs():
    with patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert MacOSApplicationPreferences().open_app_prefs("Safari") is True
    script = run.call_args.args[0][2]
    assert 'tell application "Safari" to activate' in script
    assert 'keystroke "," using command down' in script


@pytest.mark.parametrize("section,url", [
    ("accessibility", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"),
    ("automation", "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation"),
    ("notifications", "x-apple.systempreferences:com.apple.Notifications-Settings.extension"),
    ("general", "x-apple.systempreferences:com.apple.PreferenceSync.General"),
    ("unknown", "x-apple.systempreferences:com.apple.PreferenceSync.General"),
])
def test_preferences_open_system_settings(section, url):
    with patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert MacOSApplicationPreferences().open_system_settings("DeskAgent", section) is True
    run.assert_called_once_with(["open", url], check=True)


# Focus

def test_focus_activate_found_and_missing():
    service = MacOSApplicationFocus()
    target = app()
    with patch.object(service, "_get_app_by_name", return_value=target):
        assert service.activate("Safari") == {"application": "Safari", "active": True}
    target.activateWithOptions_.assert_called_once()
    with patch.object(service, "_get_app_by_name", return_value=None):
        with pytest.raises(ValueError):
            service.activate("Safari")


def test_focus_hide_show_found_and_missing():
    service = MacOSApplicationFocus()
    target = app()
    with patch.object(service, "_get_app_by_name", return_value=target):
        assert service.hide("Safari") == {"application": "Safari", "hidden": True}
        assert service.show("Safari") == {"application": "Safari", "visible": True}
    target.hide.assert_called_once_with()
    target.unhide.assert_called_once_with()
    with patch.object(service, "_get_app_by_name", return_value=None):
        assert service.hide("Safari") == {"application": "Safari", "hidden": False}
        assert service.show("Safari") == {"application": "Safari", "visible": False}


def test_focus_minimize_primary_path():
    with patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert MacOSApplicationFocus().minimize("Safari") == {"application": "Safari", "minimized": True}
    assert "AXMinimized" in run.call_args.args[0][2]


def test_focus_minimize_fallback_path():
    with patch("deskagent.platform.macos.application.subprocess.run", side_effect=[RuntimeError, None]) as run:
        assert MacOSApplicationFocus().minimize("Safari") == {"application": "Safari", "minimized": True}
    assert "miniaturized" in run.call_args_list[1].args[0][2]


def test_focus_restore_activates_after_script():
    service = MacOSApplicationFocus()
    with patch("deskagent.platform.macos.application.subprocess.run"), \
         patch.object(service, "activate") as activate:
        assert service.restore("Safari") == {"application": "Safari", "restored": True}
    activate.assert_called_once_with("Safari")


def test_focus_restore_returns_partial_when_script_fails():
    service = MacOSApplicationFocus()
    with patch("deskagent.platform.macos.application.subprocess.run", side_effect=RuntimeError), \
         patch.object(service, "activate") as activate:
        assert service.restore("Safari") == {"application": "Safari", "restored": "partial (activated only)"}
    activate.assert_called_once_with("Safari")


def test_focus_bring_to_front_delegates_to_activate():
    service = MacOSApplicationFocus()
    with patch.object(service, "activate", return_value={"application": "Safari", "active": True}) as activate:
        assert service.bring_to_front("Safari") == {"application": "Safari", "active": True}
    activate.assert_called_once_with("Safari")


def test_focus_visibility_and_focus_state():
    service = MacOSApplicationFocus()
    target = app(hidden=True)
    with patch.object(service, "_get_app_by_name", return_value=target):
        assert service.get_visibility("Safari") == {"visible": False, "hidden": True}
    with patch.object(service, "_get_app_by_name", return_value=None):
        assert service.get_visibility("Safari") == {"visible": False, "hidden": True}
    workspace = MagicMock()
    workspace.frontmostApplication.return_value = target
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        assert service.is_focused("Safari") == {"focused": True}
        assert service.is_focused("Chrome") == {"focused": False}


# Resources

def test_resources_cpu_memory_disk_aggregation():
    p1, p2 = MagicMock(), MagicMock()
    p1.cpu_percent.return_value = 2.5
    p2.cpu_percent.return_value = 3.0
    p1.memory_info.return_value.rss = 1024 * 1024
    p2.memory_info.return_value.rss = 2 * 1024 * 1024
    p1.io_counters.return_value.read_bytes = 100
    p1.io_counters.return_value.write_bytes = 200
    p2.io_counters.return_value.read_bytes = 300
    p2.io_counters.return_value.write_bytes = 400
    service = MacOSApplicationResources()
    with patch.object(service, "_get_all_matching_processes", return_value=[p1, p2]):
        assert service.get_cpu_usage("Chrome") == 5.5
        assert service.get_memory_usage("Chrome") == {"bytes": 3 * 1024 * 1024, "mb": 3.0}
        assert service.get_disk_usage("Chrome") == {"read_bytes": 400, "write_bytes": 600}


def test_resources_resource_usage_composes_methods():
    service = MacOSApplicationResources()
    with patch.object(service, "get_cpu_usage", return_value=12.5), \
         patch.object(service, "get_memory_usage", return_value={"bytes": 2048, "mb": 0.0}), \
         patch.object(service, "get_disk_usage", return_value={"read_bytes": 100, "write_bytes": 200}):
        assert service.get_resource_usage("Chrome") == {
            "cpu_percent": 12.5, "memory_bytes": 2048, "memory_mb": 0.0,
            "read_bytes": 100, "write_bytes": 200,
        }


def test_resources_top_apps_cpu_and_memory_sort_and_limit():
    p1, p2, p3 = MagicMock(), MagicMock(), MagicMock()
    p1.info = {"name": "Chrome", "cpu_percent": 30.0, "memory_info": MagicMock(rss=100)}
    p2.info = {"name": "Safari", "cpu_percent": 50.0, "memory_info": MagicMock(rss=200)}
    p3.info = {"name": "Chrome", "cpu_percent": 20.0, "memory_info": MagicMock(rss=3 * 1024 * 1024)}
    with patch("deskagent.platform.macos.application.psutil.process_iter", side_effect=[[p1, p2, p3], [p1, p2, p3]]), \
         patch("deskagent.platform.macos.application.time.sleep"):
        assert MacOSApplicationResources().get_top_resource_apps("cpu", 2) == [
            {"name": "Safari", "cpu_percent": 50.0}, {"name": "Chrome", "cpu_percent": 50.0}
        ]
    with patch("deskagent.platform.macos.application.psutil.process_iter", side_effect=[[p1, p2, p3], [p1, p2, p3]]), \
         patch("deskagent.platform.macos.application.time.sleep"):
        assert MacOSApplicationResources().get_top_resource_apps("memory", 1) == [{"name": "Chrome", "memory_mb": 3.0}]


# Processes

def test_processes_get_processes():
    p = MagicMock(pid=123)
    p.name.return_value = "Chrome Helper"
    p.cpu_percent.return_value = 7.5
    service = MacOSApplicationProcesses()
    with patch.object(service, "_find_all", return_value=[p]):
        assert service.get_processes("Chrome") == [{"pid": 123, "name": "Chrome Helper", "cpu_percent": 7.5}]


def test_processes_get_main_returns_oldest_or_none():
    old, new = MagicMock(pid=10), MagicMock(pid=20)
    old.name.return_value, new.name.return_value = "Chrome", "Chrome Helper"
    old.create_time.return_value, new.create_time.return_value = 10.0, 20.0
    service = MacOSApplicationProcesses()
    with patch.object(service, "_find_all", return_value=[new, old]):
        assert service.get_main("Chrome") == {"pid": 10, "name": "Chrome"}
    with patch.object(service, "_find_all", return_value=[]):
        assert service.get_main("Chrome") is None


def test_processes_get_children_recursive():
    child = MagicMock(pid=2)
    child.name.return_value = "helper"
    root = MagicMock(pid=1)
    root.children.return_value = [child]
    service = MacOSApplicationProcesses()
    with patch.object(service, "get_main", return_value={"pid": 1, "name": "Chrome"}), \
         patch("deskagent.platform.macos.application.psutil.Process", return_value=root):
        assert service.get_children("Chrome") == [{"pid": 2, "name": "helper"}]
    root.children.assert_called_once_with(recursive=True)


def test_processes_get_tree_builds_root_and_children():
    child = MagicMock(pid=2)
    child.name.return_value = "helper"
    child.children.return_value = []
    root = MagicMock(pid=1)
    root.name.return_value = "Chrome"
    root.children.return_value = [child]
    service = MacOSApplicationProcesses()
    with patch.object(service, "get_main", return_value={"pid": 1, "name": "Chrome"}), \
         patch("deskagent.platform.macos.application.psutil.Process", return_value=root):
        assert service.get_tree("Chrome") == {"root": {"pid": 1, "name": "Chrome", "children": [{"pid": 2, "name": "helper", "children": []}]}}


def test_processes_get_tree_returns_empty_without_main():
    service = MacOSApplicationProcesses()
    with patch.object(service, "get_main", return_value=None):
        assert service.get_tree("Chrome") == {}


def test_processes_suspend_and_resume_all_matches():
    p1, p2 = MagicMock(), MagicMock()
    service = MacOSApplicationProcesses()
    with patch.object(service, "_find_all", return_value=[p1, p2]):
        assert service.suspend("Chrome") == {"application": "Chrome", "suspended": True}
        assert service.resume("Chrome") == {"application": "Chrome", "resumed": True}
    p1.suspend.assert_called_once_with(); p2.suspend.assert_called_once_with()
    p1.resume.assert_called_once_with(); p2.resume.assert_called_once_with()


# Instances

def test_instances_get_all_and_count():
    service = MacOSApplicationInstances()
    targets = [app("Chrome", 1), app("Chrome", 2)]
    with patch.object(service, "_get_apps_by_name", return_value=targets):
        assert service.get_all("Chrome") == [{"pid": 1, "name": "Chrome"}, {"pid": 2, "name": "Chrome"}]
        assert service.get_count("Chrome") == 2


def test_instances_activate_and_quit_matching_pid():
    target = app("Chrome", 456)
    workspace = MagicMock(); workspace.runningApplications.return_value = [target]
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        assert MacOSApplicationInstances().activate("456") == {"pid": "456", "active": True}
    target.activateWithOptions_.assert_called_once()
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        assert MacOSApplicationInstances().quit(456) == {"pid": 456, "quit": True}
    target.terminate.assert_called_once_with()


def test_instances_activate_and_quit_raise_for_unknown_pid():
    workspace = MagicMock(); workspace.runningApplications.return_value = []
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        with pytest.raises(ValueError): MacOSApplicationInstances().activate(999)
    with patch("deskagent.platform.macos.application.NSWorkspace.sharedWorkspace", return_value=workspace):
        with pytest.raises(ValueError): MacOSApplicationInstances().quit(999)


# Startup

def test_startup_get_all_and_is_enabled():
    service = MacOSApplicationStartup()
    with patch("deskagent.platform.macos.application.subprocess.check_output", return_value="Slack, Dropbox, Safari"):
        assert service.get_all() == ["Slack", "Dropbox", "Safari"]
    with patch.object(service, "get_all", return_value=["Slack"]):
        assert service.is_enabled("slack") is True
        assert service.is_enabled("Safari") is False


def test_startup_get_all_returns_empty_on_error():
    with patch("deskagent.platform.macos.application.subprocess.check_output", side_effect=OSError):
        assert MacOSApplicationStartup().get_all() == []


def test_startup_add_requires_path_and_creates_item():
    service = MacOSApplicationStartup()
    with patch.object(service, "_get_app_path", return_value=None):
        with pytest.raises(FileNotFoundError): service.add("Slack")
    with patch.object(service, "_get_app_path", return_value="/Applications/Slack.app"), \
         patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert service.add("Slack") == {"application": "Slack", "added": True}
    script = run.call_args.args[0][2]
    assert "make login item" in script and "/Applications/Slack.app" in script and "hidden:false" in script


def test_startup_remove_success_and_not_found():
    with patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert MacOSApplicationStartup().remove("Slack") == {"application": "Slack", "removed": True}
    with patch("deskagent.platform.macos.application.subprocess.run", side_effect=subprocess.CalledProcessError(1, "osascript")):
        assert MacOSApplicationStartup().remove("Slack") == {"application": "Slack", "removed": False, "reason": "Not found"}


def test_startup_enable_and_disable_are_state_aware():
    service = MacOSApplicationStartup()
    with patch.object(service, "is_enabled", return_value=False), patch.object(service, "add", return_value={"application": "Slack", "added": True}) as add:
        assert service.enable("Slack") == {"application": "Slack", "added": True}
    add.assert_called_once_with("Slack")
    with patch.object(service, "is_enabled", return_value=True):
        assert service.enable("Slack") == {"application": "Slack", "enabled": True}
    with patch.object(service, "is_enabled", return_value=True), patch.object(service, "remove", return_value={"application": "Slack", "removed": True}) as remove:
        assert service.disable("Slack") == {"application": "Slack", "removed": True}
    remove.assert_called_once_with("Slack")
    with patch.object(service, "is_enabled", return_value=False):
        assert service.disable("Slack") == {"application": "Slack", "enabled": False}


# Documents

def test_documents_open_requires_existing_file_and_calls_open():
    service = MacOSApplicationDocuments()
    with patch("deskagent.platform.macos.application.os.path.exists", return_value=True), \
         patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert service.open("/tmp/a.pdf") == {"opened": True, "path": "/tmp/a.pdf"}
    run.assert_called_once_with(["open", "/tmp/a.pdf"], check=True)
    with patch("deskagent.platform.macos.application.os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError): service.open("/tmp/missing.pdf")


def test_documents_open_multiple_skips_missing_paths():
    paths = ["/tmp/a.pdf", "/tmp/missing.pdf", "/tmp/b.pdf"]
    exists = {paths[0]: True, paths[1]: False, paths[2]: True}
    with patch("deskagent.platform.macos.application.os.path.exists", side_effect=lambda p: exists[p]), \
         patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert MacOSApplicationDocuments().open_multiple(paths) == {"opened": [paths[0], paths[2]], "count": 2}
    assert run.call_args_list == [call(["open", paths[0]], check=True), call(["open", paths[2]], check=True)]


def test_documents_open_url_with_application():
    with patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert MacOSApplicationDocuments().open_url_with("https://example.com", "Chrome") == {
            "opened": True, "url": "https://example.com", "application": "Chrome"
        }
    run.assert_called_once_with(["open", "-a", "Chrome", "https://example.com"], check=True)


def test_documents_reveal_app_requires_path_and_reveals():
    service = MacOSApplicationDocuments()
    with patch.object(service, "_get_app_path", return_value=None):
        with pytest.raises(ValueError): service.reveal_app("Safari")
    with patch.object(service, "_get_app_path", return_value="/Applications/Safari.app"), \
         patch("deskagent.platform.macos.application.subprocess.run") as run:
        assert service.reveal_app("Safari") == {"revealed": True, "path": "/Applications/Safari.app"}
    run.assert_called_once_with(["open", "-R", "/Applications/Safari.app"], check=True)


def test_documents_reveal_executable_reads_info_plist(tmp_path):
    root = tmp_path / "Safari.app"
    plist = root / "Contents" / "Info.plist"
    plist.parent.mkdir(parents=True)
    with plist.open("wb") as fh:
        plistlib.dump({"CFBundleExecutable": "Safari"}, fh)
    service = MacOSApplicationDocuments()
    with patch.object(service, "_get_app_path", return_value=str(root)), \
         patch("deskagent.platform.macos.application.subprocess.run") as run:
        expected = str(root / "Contents" / "MacOS" / "Safari")
        assert service.reveal_executable("Safari") == {"revealed": True, "path": expected}
    run.assert_called_once_with(["open", "-R", expected], check=True)


def test_documents_reveal_executable_errors_for_missing_definition(tmp_path):
    root = tmp_path / "Safari.app"
    plist = root / "Contents" / "Info.plist"
    plist.parent.mkdir(parents=True)
    with plist.open("wb") as fh:
        plistlib.dump({}, fh)
    service = MacOSApplicationDocuments()
    with patch.object(service, "_get_app_path", return_value=str(root)):
        with pytest.raises(FileNotFoundError, match="executable"):
            service.reveal_executable("Safari")


def test_documents_reveal_executable_wraps_invalid_plist(tmp_path):
    root = tmp_path / "Safari.app"
    plist = root / "Contents" / "Info.plist"
    plist.parent.mkdir(parents=True)
    plist.write_bytes(b"not plist")
    service = MacOSApplicationDocuments()
    with patch.object(service, "_get_app_path", return_value=str(root)):
        with pytest.raises(RuntimeError, match="Could not find the executable"):
            service.reveal_executable("Safari")
