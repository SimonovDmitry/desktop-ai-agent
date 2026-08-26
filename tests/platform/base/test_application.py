import inspect

from deskagent.platform.base.application import (
    ApplicationDocuments,
    ApplicationFocus,
    ApplicationInformation,
    ApplicationInstances,
    ApplicationLifecycle,
    ApplicationPreferences,
    ApplicationProcesses,
    ApplicationResources,
    ApplicationStartup,
)


INTERFACES = (
    ApplicationLifecycle,
    ApplicationInformation,
    ApplicationFocus,
    ApplicationPreferences,
    ApplicationResources,
    ApplicationProcesses,
    ApplicationInstances,
    ApplicationDocuments,
    ApplicationStartup,
)


def test_application_interfaces_are_abstract():
    for cls in INTERFACES:
        assert inspect.isabstract(cls)


def test_lifecycle_interface_declares_expected_methods():
    expected = {
        "launch", "launch_hidden", "quit", "force_quit", "restart",
        "wait_for_start", "wait_for_exit", "launch_or_activate",
    }
    assert expected <= set(dir(ApplicationLifecycle))


def test_information_interface_declares_expected_methods():
    expected = {
        "get_running", "get_installed", "find", "get_info", "get_status",
        "is_running", "get_active", "get_pid", "get_path",
        "get_executable_path", "get_bundle_id", "get_version",
        "get_architecture", "get_name_from_id",
    }
    assert expected <= set(dir(ApplicationInformation))


def test_focus_interface_declares_expected_methods():
    expected = {
        "activate", "hide", "show", "minimize", "restore",
        "bring_to_front", "get_visibility", "is_focused",
    }
    assert expected <= set(dir(ApplicationFocus))


def test_preferences_interface_declares_expected_methods():
    expected = {
        "get_permissions", "get_accessibility_status", "get_automation_status",
        "get_notification_status", "get_default_app", "open_with",
        "open_app_prefs", "open_system_settings",
    }
    assert expected <= set(dir(ApplicationPreferences))


def test_resources_interface_declares_expected_methods():
    expected = {
        "get_cpu_usage", "get_memory_usage", "get_disk_usage",
        "get_resource_usage", "get_top_resource_apps",
    }
    assert expected <= set(dir(ApplicationResources))


def test_processes_interface_declares_expected_methods():
    expected = {"get_processes", "get_tree", "get_main", "get_children", "suspend", "resume"}
    assert expected <= set(dir(ApplicationProcesses))


def test_instances_interface_declares_expected_methods():
    assert {"get_all", "get_count", "activate", "quit"} <= set(dir(ApplicationInstances))


def test_documents_interface_declares_expected_methods():
    expected = {"open", "open_multiple", "open_url_with", "reveal_app", "reveal_executable"}
    assert expected <= set(dir(ApplicationDocuments))


def test_startup_interface_declares_expected_methods():
    expected = {"get_all", "is_enabled", "add", "remove", "enable", "disable"}
    assert expected <= set(dir(ApplicationStartup))
