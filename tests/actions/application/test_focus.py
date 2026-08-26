import pytest

from deskagent.actions.application.focus import (
    ActivateApplication,
    BringApplicationToFront,
    GetApplicationFocusState,
    GetApplicationVisibility,
    HideApplication,
    MinimizeApplication,
    RestoreApplication,
    ShowApplication,
)
from tests.application.conftest import assert_error, assert_success


@pytest.mark.parametrize(
    "action_cls, method, expected",
    [
        (ActivateApplication, "activate", {"application": "Safari", "active": True}),
        (HideApplication, "hide", {"application": "Safari", "hidden": True}),
        (ShowApplication, "show", {"application": "Safari", "visible": True}),
        (MinimizeApplication, "minimize", {"application": "Safari", "minimized": True}),
        (RestoreApplication, "restore", {"application": "Safari", "restored": True}),
        (BringApplicationToFront, "bring_to_front", {"application": "Safari", "front": True}),
    ],
)
def test_focus_mutation_actions(application_context, action_cls, method, expected):
    getattr(application_context.services.application, method).return_value = None

    result = action_cls().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(result, expected)
    getattr(application_context.services.application, method).assert_called_once_with(
        "Safari"
    )


def test_get_application_visibility(application_context):
    application_context.services.application.get_visibility.return_value = {
        "visible": True,
        "hidden": False,
    }

    result = GetApplicationVisibility().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(result, {"visible": True, "hidden": False})
    application_context.services.application.get_visibility.assert_called_once_with(
        "Safari"
    )


def test_get_application_focus_state(application_context):
    application_context.services.application.get_focus_state.return_value = True

    result = GetApplicationFocusState().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(result, {"focused": True})
    application_context.services.application.get_focus_state.assert_called_once_with(
        "Safari"
    )


@pytest.mark.parametrize(
    "action_cls, method",
    [
        (ActivateApplication, "activate"),
        (HideApplication, "hide"),
        (ShowApplication, "show"),
        (MinimizeApplication, "minimize"),
        (RestoreApplication, "restore"),
        (BringApplicationToFront, "bring_to_front"),
        (GetApplicationVisibility, "get_visibility"),
        (GetApplicationFocusState, "get_focus_state"),
    ],
)
def test_focus_actions_require_application(application_context, action_cls, method):
    result = action_cls().execute(application_context, {})

    assert_error(result, "MISSING_PARAM")
    getattr(application_context.services.application, method).assert_not_called()


@pytest.mark.parametrize(
    "method, action_cls",
    [
        ("activate", ActivateApplication),
        ("hide", HideApplication),
        ("show", ShowApplication),
        ("minimize", MinimizeApplication),
        ("restore", RestoreApplication),
        ("bring_to_front", BringApplicationToFront),
        ("get_visibility", GetApplicationVisibility),
        ("get_focus_state", GetApplicationFocusState),
    ],
)
def test_focus_service_errors_are_wrapped(application_context, method, action_cls):
    getattr(application_context.services.application, method).side_effect = RuntimeError("focus failed")

    result = action_cls().execute(
        application_context, {"application": "Safari"}
    )

    assert_error(result, "SYSTEM_ERROR")
    assert result.error == "focus failed"
