import logging
from unittest.mock import MagicMock

import pytest

from deskagent.core.config import Settings
from deskagent.core.context import ActionContext

# TODO добавить в platform реализацию application и привести тесты в нормальный вид и
#  все переходить к сл модулю


@pytest.fixture
def application_context():
    app = MagicMock()

    # Subservices all point to the application mock
    app.documents = app
    app.focus = app
    app.information = app
    inst = MagicMock()
    inst.get_all = app.get_instances
    inst.get_count = app.get_instance_count
    inst.activate = app.activate_instance
    inst.quit = app.quit_instance
    app.instances = inst
    app.lifecycle = app
    app.preferences = app
    app.processes = app
    app.resources = app
    app.startup = app

    # Specific method aliases where action calls differ slightly from test asserts
    app.open_document = app.open
    app.open_documents = app.open_multiple
    app.open_url_with = app.open_url_with_application
    app.reveal_app = app.reveal_application
    app.reveal_executable = app.reveal_application_executable
    app.is_focused = app.get_focus_state
    app.get_name_from_id = app.get_name

    app.get_all = app.get_login_items
    app.is_enabled = app.is_startup_enabled
    app.add = app.add_to_startup
    app.remove = app.remove_from_startup
    app.enable = app.enable_startup
    app.disable = app.disable_startup

    services = MagicMock()
    services.application = app

    return ActionContext(
        settings=Settings(),
        logger=logging.getLogger("application-actions-test"),
        services=services,
    )


def assert_success(result, data=None):
    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    if data is not None:
        assert result.data == data


def assert_error(result, error_code):
    assert result.success is False
    assert result.error_code == error_code
    assert result.error is not None
