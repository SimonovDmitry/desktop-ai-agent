import pytest

from deskagent.actions.application.preferences import (
    GetAccessibilityPermission,
    GetApplicationPermissions,
    GetAutomationPermission,
    GetDefaultApplication,
    GetNotificationPermission,
    OpenApplicationPreferences,
    OpenApplicationSystemSettings,
    OpenWithApplication,
)
from tests.application.conftest import assert_error, assert_success


@pytest.mark.parametrize(
    "action_cls, method, service_value, expected",
    [
        (
            GetApplicationPermissions,
            "get_permissions",
            {"accessibility": True, "automation": False, "notifications": True},
            {"permissions": {"accessibility": True, "automation": False, "notifications": True}},
        ),
        (GetAccessibilityPermission, "has_accessibility_permission", True, {"granted": True}),
        (GetAutomationPermission, "has_automation_permission", False, {"granted": False}),
        (GetNotificationPermission, "has_notification_permission", True, {"granted": True}),
    ],
)
def test_permission_actions(
    application_context, action_cls, method, service_value, expected
):
    getattr(application_context.services.application, method).return_value = service_value

    result = action_cls().execute(
        application_context, {"application": "DeskAgent"}
    )

    assert_success(result, expected)
    getattr(application_context.services.application, method).assert_called_once_with(
        "DeskAgent"
    )


def test_get_default_application(application_context):
    application_context.services.application.get_default_application.return_value = "Preview"

    result = GetDefaultApplication().execute(
        application_context, {"file_type": ".pdf"}
    )

    assert_success(
        result, {"file_type": ".pdf", "application": "Preview"}
    )
    application_context.services.application.get_default_application.assert_called_once_with(
        ".pdf"
    )


def test_open_with_application(application_context):
    application_context.services.application.open_with.return_value = None

    result = OpenWithApplication().execute(
        application_context,
        {"path": "/Users/me/file.pdf", "application": "Preview"},
    )

    assert_success(
        result,
        {
            "opened": True,
            "path": "/Users/me/file.pdf",
            "application": "Preview",
        },
    )
    application_context.services.application.open_with.assert_called_once_with(
        "/Users/me/file.pdf", "Preview"
    )


def test_open_application_preferences(application_context):
    application_context.services.application.open_preferences.return_value = None

    result = OpenApplicationPreferences().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(
        result, {"opened": True, "application": "Safari"}
    )
    application_context.services.application.open_preferences.assert_called_once_with(
        "Safari"
    )


def test_open_application_system_settings(application_context):
    application_context.services.application.open_system_settings.return_value = None

    result = OpenApplicationSystemSettings().execute(
        application_context,
        {"application": "DeskAgent", "section": "accessibility"},
    )

    assert_success(result, {"opened": True, "section": "accessibility"})
    application_context.services.application.open_system_settings.assert_called_once_with(
        "DeskAgent", "accessibility"
    )


@pytest.mark.parametrize(
    "action_cls, method, params",
    [
        (GetApplicationPermissions, "get_permissions", {}),
        (GetAccessibilityPermission, "has_accessibility_permission", {}),
        (GetAutomationPermission, "has_automation_permission", {}),
        (GetNotificationPermission, "has_notification_permission", {}),
        (OpenApplicationPreferences, "open_preferences", {}),
    ],
)
def test_preference_actions_require_application(
    application_context, action_cls, method, params
):
    result = action_cls().execute(application_context, params)

    assert_error(result, "MISSING_PARAM")
    getattr(application_context.services.application, method).assert_not_called()


def test_default_application_requires_file_type(application_context):
    result = GetDefaultApplication().execute(application_context, {})

    assert_error(result, "MISSING_PARAM")
    application_context.services.application.get_default_application.assert_not_called()


def test_open_with_requires_both_parameters(application_context):
    for params in (
        {},
        {"path": "/tmp/a.pdf"},
        {"application": "Preview"},
    ):
        result = OpenWithApplication().execute(application_context, params)
        assert_error(result, "MISSING_PARAM")

    application_context.services.application.open_with.assert_not_called()


def test_system_settings_requires_application_and_section(application_context):
    result = OpenApplicationSystemSettings().execute(
        application_context, {"application": "DeskAgent"}
    )

    assert_error(result, "MISSING_PARAM")
    application_context.services.application.open_system_settings.assert_not_called()


@pytest.mark.parametrize(
    "method",
    [
        "get_permissions",
        "has_accessibility_permission",
        "has_automation_permission",
        "has_notification_permission",
        "get_default_application",
        "open_with",
        "open_preferences",
        "open_system_settings",
    ],
)
def test_preference_service_errors_are_wrapped(application_context, method):
    getattr(application_context.services.application, method).side_effect = (
        RuntimeError("preference failed")
    )

    if method == "get_permissions":
        action, params = GetApplicationPermissions(), {"application": "App"}
    elif method == "has_accessibility_permission":
        action, params = GetAccessibilityPermission(), {"application": "App"}
    elif method == "has_automation_permission":
        action, params = GetAutomationPermission(), {"application": "App"}
    elif method == "has_notification_permission":
        action, params = GetNotificationPermission(), {"application": "App"}
    elif method == "get_default_application":
        action, params = GetDefaultApplication(), {"file_type": ".pdf"}
    elif method == "open_with":
        action, params = OpenWithApplication(), {"path": "/tmp/a.pdf", "application": "Preview"}
    elif method == "open_preferences":
        action, params = OpenApplicationPreferences(), {"application": "App"}
    else:
        action, params = OpenApplicationSystemSettings(), {
            "application": "App",
            "section": "accessibility",
        }

    result = action.execute(application_context, params)

    assert_error(result, "SYSTEM_ERROR")
    assert result.error == "preference failed"
