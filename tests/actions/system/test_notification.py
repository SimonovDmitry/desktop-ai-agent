from deskagent.actions.system.notification import (
    ClearAgentNotification,
    SendNotification,
)
from tests.conftest import assert_error, assert_success


def test_send_notification_requires_title_and_message(context):
    result = SendNotification().execute(context, {"title": "Title"})
    assert_error(result, "MISSING_PARAM")
    context.services.system.notify.send_notification.assert_not_called()


def test_send_notification_success(context):
    result = SendNotification().execute(
        context,
        {"title": "Title", "message": "Hello", "subtitle": "DeskAgent"},
    )
    assert_success(
        result,
        {"title": "Title", "message": "Hello", "subtitle": "DeskAgent"},
    )
    context.services.system.notify.send_notification.assert_called_once_with(
        "Title", "Hello", "DeskAgent"
    )


def test_send_notification_without_subtitle(context):
    result = SendNotification().execute(
        context, {"title": "Title", "message": "Hello"}
    )
    assert_success(
        result,
        {"title": "Title", "message": "Hello", "subtitle": None},
    )
    context.services.system.notify.send_notification.assert_called_once_with(
        "Title", "Hello", None
    )


def test_send_notification_system_error(context):
    context.services.system.notify.send_notification.side_effect = RuntimeError("notify failed")
    result = SendNotification().execute(
        context, {"title": "Title", "message": "Hello"}
    )
    assert_error(result, "SYSTEM_ERROR")


def test_clear_agent_notification_success(context):
    context.services.system.notify.clear_agent_notification.return_value = "cleared"
    result = ClearAgentNotification().execute(context, {})
    assert_success(result, {"status": "cleared"})
    context.services.system.notify.clear_agent_notification.assert_called_once_with()


def test_clear_agent_notification_system_error(context):
    context.services.system.notify.clear_agent_notification.side_effect = RuntimeError("clear failed")
    result = ClearAgentNotification().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")
