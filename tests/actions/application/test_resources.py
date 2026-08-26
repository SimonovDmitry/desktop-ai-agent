import pytest

from deskagent.actions.application.resources import (
    GetApplicationCPUUsage,
    GetApplicationDiskUsage,
    GetApplicationMemoryUsage,
    GetApplicationResourceUsage,
    GetTopResourceApplications,
)
from tests.application.conftest import assert_error, assert_success


@pytest.mark.parametrize(
    "action_cls, method, service_value, expected",
    [
        (GetApplicationCPUUsage, "get_cpu_usage", 14.5, {"cpu_percent": 14.5}),
        (
            GetApplicationMemoryUsage,
            "get_memory_usage",
            {"memory_bytes": 1258291200, "memory_mb": 1200},
            {"memory_bytes": 1258291200, "memory_mb": 1200},
        ),
        (
            GetApplicationDiskUsage,
            "get_disk_usage",
            {"read_bytes": 123456, "write_bytes": 789012},
            {"read_bytes": 123456, "write_bytes": 789012},
        ),
        (
            GetApplicationResourceUsage,
            "get_resource_usage",
            {
                "cpu_percent": 14.5,
                "memory_bytes": 1258291200,
                "read_bytes": 123456,
                "write_bytes": 789012,
            },
            {
                "cpu_percent": 14.5,
                "memory_bytes": 1258291200,
                "read_bytes": 123456,
                "write_bytes": 789012,
            },
        ),
    ],
)
def test_resource_actions(
    application_context, action_cls, method, service_value, expected
):
    getattr(application_context.services.application, method).return_value = service_value

    result = action_cls().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(result, expected)
    getattr(application_context.services.application, method).assert_called_once_with(
        "Safari"
    )


@pytest.mark.parametrize(
    "resource, limit",
    [("cpu", 10), ("memory", 5)],
)
def test_get_top_resource_applications(application_context, resource, limit):
    value = [{"name": "Safari", "value": 14.5}]
    application_context.services.application.get_top_resource_applications.return_value = value

    result = GetTopResourceApplications().execute(
        application_context,
        {"resource": resource, "limit": limit},
    )

    assert_success(
        result,
        {"resource": resource, "applications": value},
    )
    application_context.services.application.get_top_resource_applications.assert_called_once_with(
        resource, limit
    )


@pytest.mark.parametrize("resource", ["", "gpu", None])
def test_get_top_resource_applications_rejects_invalid_resource(
    application_context, resource
):
    result = GetTopResourceApplications().execute(
        application_context,
        {"resource": resource, "limit": 10},
    )

    assert_error(result, "INVALID_INPUT")
    application_context.services.application.get_top_resource_applications.assert_not_called()


@pytest.mark.parametrize("limit", [0, -1])
def test_get_top_resource_applications_rejects_invalid_limit(
    application_context, limit
):
    result = GetTopResourceApplications().execute(
        application_context,
        {"resource": "cpu", "limit": limit},
    )

    assert_error(result, "INVALID_INPUT")
    application_context.services.application.get_top_resource_applications.assert_not_called()


@pytest.mark.parametrize(
    "action_cls, method",
    [
        (GetApplicationCPUUsage, "get_cpu_usage"),
        (GetApplicationMemoryUsage, "get_memory_usage"),
        (GetApplicationDiskUsage, "get_disk_usage"),
        (GetApplicationResourceUsage, "get_resource_usage"),
    ],
)
def test_resource_actions_require_application(application_context, action_cls, method):
    result = action_cls().execute(application_context, {})

    assert_error(result, "MISSING_PARAM")
    getattr(application_context.services.application, method).assert_not_called()


def test_get_top_resource_applications_requires_resource(application_context):
    result = GetTopResourceApplications().execute(
        application_context, {"limit": 10}
    )

    assert_error(result, "MISSING_PARAM")
    application_context.services.application.get_top_resource_applications.assert_not_called()


@pytest.mark.parametrize(
    "method, action_cls",
    [
        ("get_cpu_usage", GetApplicationCPUUsage),
        ("get_memory_usage", GetApplicationMemoryUsage),
        ("get_disk_usage", GetApplicationDiskUsage),
        ("get_resource_usage", GetApplicationResourceUsage),
        ("get_top_resource_applications", GetTopResourceApplications),
    ],
)
def test_resource_service_errors_are_wrapped(application_context, method, action_cls):
    getattr(application_context.services.application, method).side_effect = RuntimeError("resource failed")

    params = {"application": "Safari"}
    if action_cls is GetTopResourceApplications:
        params = {"resource": "cpu", "limit": 10}

    result = action_cls().execute(application_context, params)

    assert_error(result, "SYSTEM_ERROR")
    assert result.error == "resource failed"
