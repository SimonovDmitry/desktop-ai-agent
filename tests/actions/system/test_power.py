import pytest

from deskagent.actions.system.power import (
    CancelShutdownComputer,
    LockScreen,
    LogoutComputer,
    RestartComputer,
    ShutdownComputer,
    SleepComputer,
)
from tests.conftest import assert_error, assert_success


@pytest.mark.parametrize(
    ("action_class", "method", "status"),
    [
        (LockScreen, "lock_screen", "locked"),
        (SleepComputer, "sleep_computer", "sleeping"),
        (RestartComputer, "restart_computer", "restarting"),
        (ShutdownComputer, "shutdown_computer", "shutting_down"),
        (LogoutComputer, "logout_computer", "logging_out"),
        (CancelShutdownComputer, "cancel_shutdown_computer", "cancelled"),
    ],
)
def test_power_action_success(context, action_class, method, status):
    result = action_class().execute(context, {})
    assert_success(result, {"status": status})
    getattr(context.services.system.power, method).assert_called_once_with()


@pytest.mark.parametrize(
    ("action_class", "method"),
    [
        (LockScreen, "lock_screen"),
        (SleepComputer, "sleep_computer"),
        (RestartComputer, "restart_computer"),
        (ShutdownComputer, "shutdown_computer"),
        (LogoutComputer, "logout_computer"),
        (CancelShutdownComputer, "cancel_shutdown_computer"),
    ],
)
def test_power_action_system_error(context, action_class, method):
    getattr(context.services.system.power, method).side_effect = RuntimeError("power failed")
    result = action_class().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")


def test_restart_requires_confirmation():
    assert RestartComputer.requires_confirmation is True


def test_shutdown_requires_confirmation():
    assert ShutdownComputer.requires_confirmation is True


def test_logout_requires_confirmation():
    assert LogoutComputer.requires_confirmation is True


def test_lock_and_sleep_do_not_require_confirmation():
    assert LockScreen.requires_confirmation is False
    assert SleepComputer.requires_confirmation is False
