import pytest

from deskagent.actions.application.information import (
    FindApplications,
    GetActiveApplication,
    GetApplicationArchitecture,
    GetApplicationBundleId,
    GetApplicationExecutablePath,
    GetApplicationInfo,
    GetApplicationName,
    GetApplicationPID,
    GetApplicationPath,
    GetApplicationStatus,
    GetApplicationVersion,
    GetInstalledApplications,
    GetRunningApplications,
    IsApplicationRunning,
)
from tests.application.conftest import assert_error, assert_success


def test_get_running_applications_success(application_context):
    value = [{"name": "Safari", "pid": 123, "bundle_id": "com.apple.Safari"}]
    application_context.services.application.get_running.return_value = value

    result = GetRunningApplications().execute(application_context, {})

    assert_success(result, {"applications": value})
    application_context.services.application.get_running.assert_called_once_with()


def test_get_installed_applications_success(application_context):
    value = [{"name": "Safari", "bundle_id": "com.apple.Safari"}]
    application_context.services.application.get_installed.return_value = value

    result = GetInstalledApplications().execute(application_context, {})

    assert_success(result, {"applications": value})
    application_context.services.application.get_installed.assert_called_once_with()


@pytest.mark.parametrize(
    "params, expected_call",
    [
        ({"query": "chrome"}, ("chrome", None)),
        ({"query": "browser", "limit": 10}, ("browser", 10)),
    ],
)
def test_find_applications_forwards_query_and_optional_limit(
    application_context, params, expected_call
):
    value = [{"name": "Google Chrome"}]
    application_context.services.application.find.return_value = value

    result = FindApplications().execute(application_context, params)

    assert_success(result, {"applications": value})
    application_context.services.application.find.assert_called_once_with(*expected_call)


@pytest.mark.parametrize("params", [{}, {"query": None}, {"query": ""}])
def test_find_applications_rejects_missing_query(application_context, params):
    result = FindApplications().execute(application_context, params)

    assert_error(result, "MISSING_PARAM")
    application_context.services.application.find.assert_not_called()


def test_get_application_info_success(application_context):
    value = {
        "name": "Safari",
        "pid": 123,
        "path": "/Applications/Safari.app",
        "bundle_id": "com.apple.Safari",
        "version": "18.5",
        "architecture": "arm64",
    }
    application_context.services.application.get_info.return_value = value

    result = GetApplicationInfo().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(result, value)
    application_context.services.application.get_info.assert_called_once_with("Safari")


def test_get_application_status_success(application_context):
    value = {"running": True, "visible": True, "active": True, "pid": 123}
    application_context.services.application.get_status.return_value = value

    result = GetApplicationStatus().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(result, value)
    application_context.services.application.get_status.assert_called_once_with("Safari")


def test_is_application_running_success(application_context):
    application_context.services.application.is_running.return_value = True

    result = IsApplicationRunning().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(result, {"running": True})
    application_context.services.application.is_running.assert_called_once_with("Safari")


def test_get_active_application_success(application_context):
    value = {"name": "Safari", "pid": 123, "bundle_id": "com.apple.Safari"}
    application_context.services.application.get_active.return_value = value

    result = GetActiveApplication().execute(application_context, {})

    assert_success(result, value)
    application_context.services.application.get_active.assert_called_once_with()


@pytest.mark.parametrize(
    "action_cls, service_method, expected_data, service_value",
    [
        (GetApplicationPID, "get_pid", {"pid": 12345}, 12345),
        (GetApplicationPath, "get_path", {"path": "/Applications/Safari.app"}, "/Applications/Safari.app"),
        (
            GetApplicationExecutablePath,
            "get_executable_path",
            {"executable": "/Applications/Safari.app/Contents/MacOS/Safari"},
            "/Applications/Safari.app/Contents/MacOS/Safari",
        ),
        (
            GetApplicationBundleId,
            "get_bundle_id",
            {"bundle_id": "com.apple.Safari"},
            "com.apple.Safari",
        ),
        (GetApplicationVersion, "get_version", {"version": "18.5"}, "18.5"),
        (
            GetApplicationArchitecture,
            "get_architecture",
            {"architecture": "arm64"},
            "arm64",
        ),
        (GetApplicationName, "get_name", {"name": "Safari"}, "Safari"),
    ],
)
def test_application_scalar_information_actions(
    application_context, action_cls, service_method, expected_data, service_value
):
    getattr(application_context.services.application, service_method).return_value = service_value

    params = {"application": "Safari"}
    if action_cls is GetApplicationName:
        params = {"identifier_type": "pid", "identifier": 12345}

    result = action_cls().execute(application_context, params)

    assert_success(result, expected_data)
    if action_cls is GetApplicationName:
        getattr(application_context.services.application, service_method).assert_called_once_with(
            "pid", 12345
        )
    else:
        getattr(application_context.services.application, service_method).assert_called_once_with(
            "Safari"
        )


@pytest.mark.parametrize(
    "action_cls, service_method",
    [
        (GetApplicationInfo, "get_info"),
        (GetApplicationStatus, "get_status"),
        (GetApplicationPID, "get_pid"),
        (GetApplicationPath, "get_path"),
        (GetApplicationExecutablePath, "get_executable_path"),
        (GetApplicationBundleId, "get_bundle_id"),
        (GetApplicationVersion, "get_version"),
        (GetApplicationArchitecture, "get_architecture"),
    ],
)
def test_application_lookup_actions_require_application(
    application_context, action_cls, service_method
):
    result = action_cls().execute(application_context, {})

    assert_error(result, "MISSING_PARAM")
    getattr(application_context.services.application, service_method).assert_not_called()


def test_is_application_running_requires_application(application_context):
    result = IsApplicationRunning().execute(application_context, {})

    assert_error(result, "MISSING_PARAM")
    application_context.services.application.is_running.assert_not_called()


def test_get_application_name_requires_identifier(application_context):
    result = GetApplicationName().execute(application_context, {})

    assert_error(result, "MISSING_PARAM")
    application_context.services.application.get_name.assert_not_called()


@pytest.mark.parametrize(
    "action_cls, service_method",
    [
        (GetRunningApplications, "get_running"),
        (GetInstalledApplications, "get_installed"),
        (GetActiveApplication, "get_active"),
    ],
)
def test_information_actions_convert_service_exception_to_system_error(
    application_context, action_cls, service_method
):
    getattr(application_context.services.application, service_method).side_effect = (
        RuntimeError("application service failed")
    )

    result = action_cls().execute(application_context, {})

    assert_error(result, "SYSTEM_ERROR")
    assert result.error == "application service failed"


def test_get_application_info_preserves_service_data(application_context):
    value = {
        "name": "MyApp",
        "pid": 7,
        "path": "/Applications/MyApp.app",
        "bundle_id": "com.example.myapp",
        "version": "1.2.3",
        "architecture": "universal",
    }
    application_context.services.application.get_info.return_value = value

    result = GetApplicationInfo().execute(
        application_context, {"application": "MyApp"}
    )

    assert_success(result, value)
