import pytest

from deskagent.actions.application.lifecycle import (
    ForceQuitApplication,
    LaunchApplication,
    LaunchApplicationHidden,
    LaunchApplicationWithArguments,
    LaunchOrActivateApplication,
    QuitApplication,
    RestartApplication,
    WaitForApplication,
    WaitForApplicationExit,
)
from deskagent.actions.types import RiskLevel
from tests.application.conftest import assert_error, assert_success


def test_launch_application_success(application_context):
    application_context.services.application.launch.return_value = 12345

    result = LaunchApplication().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(
        result,
        {"application": "Safari", "pid": 12345, "launched": True},
    )
    application_context.services.application.launch.assert_called_once_with("Safari")


def test_launch_application_with_arguments_forwards_arguments(application_context):
    application_context.services.application.launch.return_value = 12345
    args = ["--new-window", "https://google.com"]

    result = LaunchApplicationWithArguments().execute(
        application_context,
        {"application": "Google Chrome", "arguments": args},
    )

    assert_success(
        result,
        {"application": "Google Chrome", "pid": 12345, "launched": True},
    )
    application_context.services.application.launch.assert_called_once_with(
        "Google Chrome", arguments=args
    )


def test_launch_application_hidden_success(application_context):
    application_context.services.application.launch_hidden.return_value = 12345

    result = LaunchApplicationHidden().execute(
        application_context, {"application": "Terminal"}
    )

    assert_success(
        result,
        {
            "application": "Terminal",
            "pid": 12345,
            "launched": True,
            "hidden": True,
        },
    )
    application_context.services.application.launch_hidden.assert_called_once_with(
        "Terminal"
    )


@pytest.mark.parametrize(
    "action_cls, method, expected_data",
    [
        (QuitApplication, "quit", {"application": "Safari", "quit": True}),
        (
            ForceQuitApplication,
            "force_quit",
            {"application": "Safari", "terminated": True},
        ),
        (
            RestartApplication,
            "restart",
            {"application": "Safari", "restarted": True},
        ),
    ],
)
def test_lifecycle_actions_success(
    application_context, action_cls, method, expected_data
):
    getattr(application_context.services.application, method).return_value = None

    result = action_cls().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(result, expected_data)
    getattr(application_context.services.application, method).assert_called_once_with(
        "Safari"
    )


def test_wait_for_application_success(application_context):
    application_context.services.application.wait_for_start.return_value = {
        "started": True,
        "pid": 12345,
        "waited": 4.2,
    }

    result = WaitForApplication().execute(
        application_context, {"application": "Photoshop", "timeout": 30}
    )

    assert_success(
        result,
        {
            "application": "Photoshop",
            "started": True,
            "pid": 12345,
            "waited": 4.2,
        },
    )
    application_context.services.application.wait_for_start.assert_called_once_with(
        "Photoshop", 30
    )


def test_wait_for_application_exit_success(application_context):
    application_context.services.application.wait_for_exit.return_value = {
        "exited": True,
        "waited": 2.5,
    }

    result = WaitForApplicationExit().execute(
        application_context, {"application": "Safari", "timeout": 30}
    )

    assert_success(
        result,
        {"application": "Safari", "exited": True, "waited": 2.5},
    )
    application_context.services.application.wait_for_exit.assert_called_once_with(
        "Safari", 30
    )


@pytest.mark.parametrize(
    "action_cls, method, params",
    [
        (LaunchApplication, "launch", {}),
        (LaunchApplicationWithArguments, "launch", {"application": "Chrome"}),
        (LaunchApplicationHidden, "launch_hidden", {}),
        (QuitApplication, "quit", {}),
        (ForceQuitApplication, "force_quit", {}),
        (RestartApplication, "restart", {}),
        (WaitForApplication, "wait_for_start", {"application": "Safari"}),
        (WaitForApplicationExit, "wait_for_exit", {"application": "Safari"}),
        (LaunchOrActivateApplication, "launch_or_activate", {}),
    ],
)
def test_lifecycle_actions_require_application(
    application_context, action_cls, method, params
):
    result = action_cls().execute(application_context, params)

    assert_error(result, "MISSING_PARAM")
    getattr(application_context.services.application, method).assert_not_called()


def test_wait_actions_reject_invalid_timeout(application_context):
    for action_cls in (WaitForApplication, WaitForApplicationExit):
        result = action_cls().execute(
            application_context, {"application": "Safari", "timeout": 0}
        )
        assert_error(result, "INVALID_INPUT")

    application_context.services.application.wait_for_start.assert_not_called()
    application_context.services.application.wait_for_exit.assert_not_called()


@pytest.mark.parametrize(
    "method",
    [
        "launch",
        "launch_hidden",
        "quit",
        "force_quit",
        "restart",
        "wait_for_start",
        "wait_for_exit",
        "launch_or_activate",
    ],
)
def test_lifecycle_service_errors_are_wrapped(
    application_context, method
):
    getattr(application_context.services.application, method).side_effect = (
        RuntimeError("boom")
    )

    if method == "launch":
        action = LaunchApplication()
        params = {"application": "Safari"}
    elif method == "launch_hidden":
        action = LaunchApplicationHidden()
        params = {"application": "Safari"}
    elif method == "quit":
        action = QuitApplication()
        params = {"application": "Safari"}
    elif method == "force_quit":
        action = ForceQuitApplication()
        params = {"application": "Safari"}
    elif method == "restart":
        action = RestartApplication()
        params = {"application": "Safari"}
    elif method == "wait_for_start":
        action = WaitForApplication()
        params = {"application": "Safari", "timeout": 30}
    elif method == "wait_for_exit":
        action = WaitForApplicationExit()
        params = {"application": "Safari", "timeout": 30}
    else:
        action = LaunchOrActivateApplication()
        params = {"application": "Safari"}

    result = action.execute(application_context, params)

    assert_error(result, "SYSTEM_ERROR")
    assert result.error == "boom"


def test_launch_or_activate_returns_platform_decision(application_context):
    application_context.services.application.launch_or_activate.return_value = {
        "action": "activated",
        "pid": 12345,
    }

    result = LaunchOrActivateApplication().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(
        result,
        {"application": "Safari", "action": "activated", "pid": 12345},
    )


def test_force_quit_has_confirmation_and_medium_risk():
    action = ForceQuitApplication()

    assert action.requires_confirmation is True
    assert action.risk_level is RiskLevel.MEDIUM


@pytest.mark.parametrize(
    "action_cls",
    [
        LaunchApplication,
        LaunchApplicationWithArguments,
        LaunchApplicationHidden,
        QuitApplication,
        RestartApplication,
        WaitForApplication,
        WaitForApplicationExit,
        LaunchOrActivateApplication,
    ],
)
def test_non_force_lifecycle_actions_do_not_require_confirmation(action_cls):
    assert action_cls().requires_confirmation is False
