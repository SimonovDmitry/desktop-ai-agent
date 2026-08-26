import pytest

from deskagent.actions.application.instances import (
    ActivateApplicationInstance,
    GetApplicationInstanceCount,
    GetApplicationInstances,
    QuitApplicationInstance,
)
from tests.application.conftest import assert_error, assert_success


def test_get_application_instances(application_context):
    value = [
        {"pid": 123, "name": "Google Chrome"},
        {"pid": 456, "name": "Google Chrome"},
    ]
    application_context.services.application.get_instances.return_value = value

    result = GetApplicationInstances().execute(
        application_context, {"application": "Google Chrome"}
    )

    assert_success(result, {"instances": value})
    application_context.services.application.get_instances.assert_called_once_with(
        "Google Chrome"
    )


def test_get_application_instance_count(application_context):
    application_context.services.application.get_instance_count.return_value = 2

    result = GetApplicationInstanceCount().execute(
        application_context, {"application": "Google Chrome"}
    )

    assert_success(result, {"count": 2})
    application_context.services.application.get_instance_count.assert_called_once_with(
        "Google Chrome"
    )


@pytest.mark.parametrize(
    "action_cls, method, key",
    [
        (ActivateApplicationInstance, "activate_instance", "active"),
        (QuitApplicationInstance, "quit_instance", "quit"),
    ],
)
def test_application_instance_mutations(
    application_context, action_cls, method, key
):
    getattr(application_context.services.application, method).return_value = None

    result = action_cls().execute(
        application_context,
        {"application": "Google Chrome", "pid": 456},
    )

    assert_success(result, {"pid": 456, key: True})
    getattr(application_context.services.application, method).assert_called_once_with(
        "Google Chrome", 456
    )


@pytest.mark.parametrize(
    "action_cls, method",
    [
        (GetApplicationInstances, "get_instances"),
        (GetApplicationInstanceCount, "get_instance_count"),
        (ActivateApplicationInstance, "activate_instance"),
        (QuitApplicationInstance, "quit_instance"),
    ],
)
def test_instance_actions_require_application(application_context, action_cls, method):
    result = action_cls().execute(
        application_context, {}
    )

    assert_error(result, "MISSING_PARAM")
    getattr(application_context.services.application, method).assert_not_called()


@pytest.mark.parametrize(
    "action_cls",
    [ActivateApplicationInstance, QuitApplicationInstance],
)
def test_instance_mutations_require_pid(application_context, action_cls):
    result = action_cls().execute(
        application_context, {"application": "Google Chrome"}
    )

    assert_error(result, "MISSING_PARAM")
    application_context.services.application.activate_instance.assert_not_called()
    application_context.services.application.quit_instance.assert_not_called()


@pytest.mark.parametrize(
    "method, action_cls, params",
    [
        ("get_instances", GetApplicationInstances, {"application": "Chrome"}),
        ("get_instance_count", GetApplicationInstanceCount, {"application": "Chrome"}),
        ("activate_instance", ActivateApplicationInstance, {"application": "Chrome", "pid": 1}),
        ("quit_instance", QuitApplicationInstance, {"application": "Chrome", "pid": 1}),
    ],
)
def test_instance_service_errors_are_wrapped(
    application_context, method, action_cls, params
):
    getattr(application_context.services.application, method).side_effect = RuntimeError("instance failed")

    result = action_cls().execute(application_context, params)

    assert_error(result, "SYSTEM_ERROR")
    assert result.error == "instance failed"
