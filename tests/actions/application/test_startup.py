import pytest

from deskagent.actions.application.startup import (
    AddApplicationToStartup,
    DisableApplicationStartup,
    EnableApplicationStartup,
    GetLoginItems,
    IsApplicationStartupEnabled,
    RemoveApplicationFromStartup,
)
from deskagent.actions.types import RiskLevel
from tests.application.conftest import assert_error, assert_success


def test_get_login_items(application_context):
    value = [{"name": "Slack"}, {"name": "Raycast"}]
    application_context.services.application.get_login_items.return_value = value

    result = GetLoginItems().execute(application_context, {})

    assert_success(result, {"applications": value})
    application_context.services.application.get_login_items.assert_called_once_with()


def test_is_application_startup_enabled(application_context):
    application_context.services.application.is_startup_enabled.return_value = True

    result = IsApplicationStartupEnabled().execute(
        application_context, {"application": "Slack"}
    )

    assert_success(result, {"enabled": True})
    application_context.services.application.is_startup_enabled.assert_called_once_with(
        "Slack"
    )


@pytest.mark.parametrize(
    "action_cls, method, key, value",
    [
        (AddApplicationToStartup, "add_to_startup", "added", True),
        (RemoveApplicationFromStartup, "remove_from_startup", "removed", True),
        (EnableApplicationStartup, "enable_startup", "enabled", True),
        (DisableApplicationStartup, "disable_startup", "enabled", False),
    ],
)
def test_startup_mutation_actions(
    application_context, action_cls, method, key, value
):
    getattr(application_context.services.application, method).return_value = None

    result = action_cls().execute(
        application_context, {"application": "Slack"}
    )

    assert_success(result, {"application": "Slack", key: value})
    getattr(application_context.services.application, method).assert_called_once_with(
        "Slack"
    )


@pytest.mark.parametrize(
    "action_cls",
    [
        AddApplicationToStartup,
        RemoveApplicationFromStartup,
        EnableApplicationStartup,
        DisableApplicationStartup,
        IsApplicationStartupEnabled,
    ],
)
def test_startup_application_actions_require_application(
    application_context, action_cls
):
    method_map = {
        AddApplicationToStartup: "add_to_startup",
        RemoveApplicationFromStartup: "remove_from_startup",
        EnableApplicationStartup: "enable_startup",
        DisableApplicationStartup: "disable_startup",
        IsApplicationStartupEnabled: "is_startup_enabled",
    }
    method = method_map[action_cls]

    result = action_cls().execute(application_context, {})

    assert_error(result, "MISSING_PARAM")
    getattr(application_context.services.application, method).assert_not_called()


def test_add_application_to_startup_requires_confirmation_and_medium_risk():
    action = AddApplicationToStartup()
    assert action.requires_confirmation is True
    assert action.risk_level is RiskLevel.MEDIUM


@pytest.mark.parametrize(
    "action_cls",
    [RemoveApplicationFromStartup, EnableApplicationStartup, DisableApplicationStartup],
)
def test_other_startup_mutations_are_safe_by_confirmation_default(action_cls):
    assert action_cls().requires_confirmation is False


@pytest.mark.parametrize(
    "method, action_cls, params",
    [
        ("get_login_items", GetLoginItems, {}),
        ("is_startup_enabled", IsApplicationStartupEnabled, {"application": "Slack"}),
        ("add_to_startup", AddApplicationToStartup, {"application": "Slack"}),
        ("remove_from_startup", RemoveApplicationFromStartup, {"application": "Slack"}),
        ("enable_startup", EnableApplicationStartup, {"application": "Slack"}),
        ("disable_startup", DisableApplicationStartup, {"application": "Slack"}),
    ],
)
def test_startup_service_errors_are_wrapped(
    application_context, method, action_cls, params
):
    getattr(application_context.services.application, method).side_effect = RuntimeError("startup failed")

    result = action_cls().execute(application_context, params)

    assert_error(result, "SYSTEM_ERROR")
    assert result.error == "startup failed"
