import pytest

from deskagent.actions.application.processes import (
    GetApplicationChildProcesses,
    GetApplicationMainProcess,
    GetApplicationProcessTree,
    GetApplicationProcesses,
    ResumeApplication,
    SuspendApplication,
)
from deskagent.actions.types import RiskLevel
from tests.application.conftest import assert_error, assert_success


@pytest.mark.parametrize(
    "action_cls, method, value, expected",
    [
        (
            GetApplicationProcesses,
            "get_processes",
            [{"pid": 123, "name": "Google Chrome", "cpu_percent": 5.2}],
            {"processes": [{"pid": 123, "name": "Google Chrome", "cpu_percent": 5.2}]},
        ),
        (
            GetApplicationProcessTree,
            "get_process_tree",
            {"root": {"pid": 123}, "children": [{"pid": 456}]},
            {"root": {"pid": 123}, "children": [{"pid": 456}]},
        ),
        (
            GetApplicationMainProcess,
            "get_main_process",
            {"pid": 123, "name": "Google Chrome"},
            {"pid": 123, "name": "Google Chrome"},
        ),
        (
            GetApplicationChildProcesses,
            "get_child_processes",
            [{"pid": 456, "name": "Renderer"}],
            {"processes": [{"pid": 456, "name": "Renderer"}]},
        ),
    ],
)
def test_process_query_actions(
    application_context, action_cls, method, value, expected
):
    getattr(application_context.services.application, method).return_value = value

    result = action_cls().execute(
        application_context, {"application": "Chrome"}
    )

    assert_success(result, expected)
    getattr(application_context.services.application, method).assert_called_once_with(
        "Chrome"
    )


@pytest.mark.parametrize(
    "action_cls, method, key, expected",
    [
        (SuspendApplication, "suspend", "suspended", True),
        (ResumeApplication, "resume", "resumed", True),
    ],
)
def test_process_control_actions(
    application_context, action_cls, method, key, expected
):
    getattr(application_context.services.application, method).return_value = None

    result = action_cls().execute(
        application_context, {"application": "Chrome"}
    )

    assert_success(result, {"application": "Chrome", key: expected})
    getattr(application_context.services.application, method).assert_called_once_with(
        "Chrome"
    )


@pytest.mark.parametrize(
    "action_cls, method",
    [
        (GetApplicationProcesses, "get_processes"),
        (GetApplicationProcessTree, "get_process_tree"),
        (GetApplicationMainProcess, "get_main_process"),
        (GetApplicationChildProcesses, "get_child_processes"),
        (SuspendApplication, "suspend"),
        (ResumeApplication, "resume"),
    ],
)
def test_process_actions_require_application(application_context, action_cls, method):
    result = action_cls().execute(application_context, {})

    assert_error(result, "MISSING_PARAM")
    getattr(application_context.services.application, method).assert_not_called()


def test_suspend_application_has_confirmation_and_medium_risk():
    action = SuspendApplication()
    assert action.requires_confirmation is True
    assert action.risk_level is RiskLevel.MEDIUM


def test_resume_application_does_not_require_confirmation():
    assert ResumeApplication().requires_confirmation is False


@pytest.mark.parametrize(
    "method, action_cls",
    [
        ("get_processes", GetApplicationProcesses),
        ("get_process_tree", GetApplicationProcessTree),
        ("get_main_process", GetApplicationMainProcess),
        ("get_child_processes", GetApplicationChildProcesses),
        ("suspend", SuspendApplication),
        ("resume", ResumeApplication),
    ],
)
def test_process_service_errors_are_wrapped(application_context, method, action_cls):
    getattr(application_context.services.application, method).side_effect = RuntimeError("process failed")

    result = action_cls().execute(
        application_context, {"application": "Chrome"}
    )

    assert_error(result, "SYSTEM_ERROR")
    assert result.error == "process failed"
